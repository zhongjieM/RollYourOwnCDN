.PHONY: target
target:
	wget https://www.yingquanyuan.com/static/fcn/db_geoip.zip; unzip db_geoip.zip; rm db_geoip.zip
	python src/geoiptool/geoip_splitter.py -s ./db_geoip -d .
	ln -sf src/dnsserver/dnsserver.py dnsserver
	ln -sf src/httpserver/httpserver.py httpserver
	ln -sf deploy/deployCDN.sh deployCDN
	ln -sf deploy/runCDN.sh runCDN
	ln -sf deploy/stopCDN.sh stopCDN

.PHONY: clean
clean:
	find . \( -name "*.pyc" \) -exec rm {} \;
	rm -f dnsserver httpserver deployCDN runCDN stopCDN
	rm -rf db_geoip blocks locations
