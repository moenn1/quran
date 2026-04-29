FROM nginx:1.27-alpine

ARG API_BASE_URL=http://localhost:8000

COPY docker/web/nginx.conf /etc/nginx/conf.d/default.conf
COPY docker/web/index.html /usr/share/nginx/html/index.html

RUN sed -i "s|__API_BASE_URL__|${API_BASE_URL}|g" /usr/share/nginx/html/index.html

EXPOSE 80
