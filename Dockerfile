# マルチプラットフォーム対応
FROM python:3.13-slim

# 作業ディレクトリ設定
WORKDIR /app

# システムパッケージ更新・必要パッケージインストール
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係コピー・インストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# プロジェクトファイルコピー
COPY . .

# 静的ファイル・メディアファイル用ディレクトリ作成
RUN mkdir -p static media

# ポート公開
EXPOSE 8000

# デフォルトコマンド
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
