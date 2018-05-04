
build:
	docker build -t lc-nginx .

run:
	cd static; python gen_plot_json.py
	docker run --name lc-nginx-1 -v /dhome/chchen/KDDCUP2018/KDDCUP2018/d3_dailyplot/static:/usr/share/nginx/html -p 8081:80 -d lc-nginx

rm:
	docker rm -f lc-nginx-1


