import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    use_https = os.environ.get("USE_HTTPS", "false").lower() == "true"

    if use_https:
        app.run(host='0.0.0.0', port=port, ssl_context=('cert.pem', 'key.pem'))
    else:
        app.run(host='0.0.0.0', port=port)
