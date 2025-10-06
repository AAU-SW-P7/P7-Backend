CREATE TABLE "users" (
  "id" SERIAL PRIMARY KEY
);

CREATE TABLE "service" (
  "id" SERIAL PRIMARY KEY,
  "userId" BIGINT NOT NULL,
  "oauthType" TEXT NOT NULL,
  "oauthToken" TEXT NOT NULL,
  "accessToken" TEXT NOT NULL,
  "accessTokenExpiration" TIMESTAMPTZ NOT NULL,
  "refreshToken" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "accountId" TEXT NOT NULL,
  "email" TEXT NOT NULL,
  "scopeName" TEXT NOT NULL
);

CREATE TABLE "file" (
  "id" SERIAL PRIMARY KEY,
  "serviceId" BIGINT NOT NULL,
  "serviceFileId" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "extension" TEXT NOT NULL,
  "downloadable" BOOLEAN NOT NULL,
  "path" TEXT NOT NULL,
  "link" TEXT NOT NULL,
  "size" BIGINT NOT NULL,
  "createdAt" TIMESTAMPTZ NOT NULL,
  "modifiedAt" TIMESTAMPTZ NOT NULL,
  "lastIndexed" TIMESTAMPTZ,
  "snippet" TEXT,
  "content" TEXT
);

CREATE TABLE "term" (
  "id" SERIAL PRIMARY KEY,
  "termName" TEXT NOT NULL,
  "documentFrequency" BIGINT NOT NULL
);

CREATE TABLE "invertedindex" (
  "id" SERIAL PRIMARY KEY,
  "userId" BIGINT NOT NULL,
  "termId" BIGINT NOT NULL
);

CREATE TABLE "posting" (
  "id" SERIAL PRIMARY KEY,
  "termId" BIGINT NOT NULL,
  "fileId" BIGINT NOT NULL,
  "termFrequency" BIGINT NOT NULL
);

CREATE UNIQUE INDEX "uq_service_file_id" ON "file" ("serviceId", "serviceFileId");

CREATE UNIQUE INDEX "uq_inv_user_term" ON "invertedindex" ("userId", "termId");

ALTER TABLE "service" ADD CONSTRAINT "fk_service_user" FOREIGN KEY ("userId") REFERENCES "users" ("id") ON DELETE CASCADE;

ALTER TABLE "file" ADD CONSTRAINT "fk_file_service" FOREIGN KEY ("serviceId") REFERENCES "service" ("id") ON DELETE CASCADE;

ALTER TABLE "invertedindex" ADD CONSTRAINT "fk_inv_user" FOREIGN KEY ("userId") REFERENCES "users" ("id") ON DELETE CASCADE;

ALTER TABLE "invertedindex" ADD CONSTRAINT "fk_inv_term" FOREIGN KEY ("termId") REFERENCES "term" ("id") ON DELETE CASCADE;

ALTER TABLE "posting" ADD CONSTRAINT "fk_posting_term" FOREIGN KEY ("termId") REFERENCES "term" ("id") ON DELETE CASCADE;

ALTER TABLE "posting" ADD CONSTRAINT "fk_posting_file" FOREIGN KEY ("fileId") REFERENCES "file" ("id") ON DELETE CASCADE;