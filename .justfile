# Builds and publishes a new version of the scraper
build-scraper VERSION:
    docker build -t ghcr.io/dav354/scraper:latest . && \
    docker tag ghcr.io/dav354/scraper:latest ghcr.io/dav354/scraper:{{VERSION}} && \
    docker push ghcr.io/dav354/scraper:latest && \
    docker push ghcr.io/dav354/scraper:{{VERSION}}

# formats the files
fmt:
    pre-commit run --all-files

# compresses the data as tar.xz
compress FILE:
    tar -cf "{{without_extension(FILE)}}.tar.xz" \
        -I "xz -9 --threads=0" \
        "{{FILE}}"

# Shows the csv as nice table in the cli
show FILE:
    column -t -s, {{FILE}} | less -S

# Summarize stats CSV: totals for Html, Pdf, Ical, Errors, Empty, Ignored, Bytes
summarize FILE:
    awk -F, 'NR>1 {v=$8; sub(/ KB$$/,"",v); html+=$2; pdf+=$3; ical+=$4; errors+=$5; empty+=$6; ignored+=$7; kb+=v} END {unit="KB"; val=kb; if(kb>=1024*1024){val=kb/(1024*1024); unit="GB"} else if(kb>=1024){val=kb/1024; unit="MB"}; printf "Html: %d, Pdf: %d, Ical: %d, Errors: %d, Empty: %d, Ignored: %d, Bytes: %.1f %s\n", html,pdf,ical,errors,empty,ignored,val,unit}' {{FILE}}

# Cleans the logfile for further inspection
clean-logs FILE:
    echo "Removing lines containing 'scrapy.extensions.logstats'" && \
    sed -i '/scrapy\.extensions\.logstats/d' {{FILE}} && \
    echo "Removing lines containing 'uploads' (forbidden path by robots.txt)" && \
    sed -i '/uploads/d' {{FILE}} && \
    echo "Removing lines for 'git.fix.thws.de (forbidden by robots.txt)" && \
    sed -i '/git\.fiw\.thws\.de/d' {{FILE}} && \
    echo "Removing 503 Service Unavailable" && \
    sed -i '/503 Service Unavailable/d' {{FILE}} && \
    echo "Removing 500 Internal Server" && \
    sed -i '/500 Internal Server/d' {{FILE}} && \
    echo "Removing Emty Text Warning" && \
    sed -i '/^[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\} [0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\},[0-9]\{3\} \[WARNING\] scrapy\.core\.scraper: Dropped: Empty text - dropping/,/^}/d' {{FILE}} && \
    echo "Remove 'Received more bytes than download warn size'" && \
    sed -i '/Received more bytes than download warn size/d' {{FILE}} && \
    echo "Remove Timeout Error" && \
    sed -i '/TimeoutError/d' {{FILE}} && \
    sed -i '/larger than download warn size/d' {{FILE}}
