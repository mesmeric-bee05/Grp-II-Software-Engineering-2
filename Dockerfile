FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=3000 DEBUG=0 ALLOWED_HOSTS=.a.run.app,.manus.space,.manus.computer,127.0.0.1,localhost CSRF_TRUSTED_ORIGINS=https://*.manus.space,https://*.manus.computer
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python -c "import secrets; open('/app/.runtime-secret', 'w', encoding='utf-8').write(secrets.token_urlsafe(64))" && chmod 0600 /app/.runtime-secret && chmod 0755 /app/entrypoint.sh && python manage.py collectstatic --noinput
EXPOSE 3000
ENTRYPOINT ["/bin/sh", "/app/entrypoint.sh"]
