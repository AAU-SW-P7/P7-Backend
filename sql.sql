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
  "termName" TEXT NOT NULL
);

CREATE TABLE "invertedindex" (
  "userId" BIGINT NOT NULL,
  "termName" TEXT NOT NULL,
  "documentFrequency" BIGINT NOT NULL
);

CREATE TABLE "posting" (
  "termName" TEXT NOT NULL,
  "fileId" BIGINT NOT NULL,
  "termFrequency" BIGINT NOT NULL
);

CREATE UNIQUE INDEX "uq_service_file_id" ON "file" ("serviceId", "serviceFileId");

CREATE UNIQUE INDEX "uq_term_name" ON "term" ("termName");

CREATE UNIQUE INDEX "uq_inv_user_term_name" ON "invertedindex" ("userId", "termName");

CREATE UNIQUE INDEX "uq_term_name_file_id" ON "posting" ("termName", "fileId");

ALTER TABLE "service" ADD CONSTRAINT "fk_service_user" FOREIGN KEY ("userId") REFERENCES "users" ("id") ON DELETE CASCADE;

ALTER TABLE "file" ADD CONSTRAINT "fk_file_service" FOREIGN KEY ("serviceId") REFERENCES "service" ("id") ON DELETE CASCADE;

CREATE TABLE "users_invertedindex" (
  "users_id" SERIAL,
  "invertedindex_userId" BIGINT,
  PRIMARY KEY ("users_id", "invertedindex_userId")
);

ALTER TABLE "users_invertedindex" ADD FOREIGN KEY ("users_id") REFERENCES "users" ("id");

ALTER TABLE "users_invertedindex" ADD FOREIGN KEY ("invertedindex_userId") REFERENCES "invertedindex" ("userId");


CREATE TABLE "term_posting" (
  "term_termName" TEXT,
  "posting_termName" TEXT,
  PRIMARY KEY ("term_termName", "posting_termName")
);

ALTER TABLE "term_posting" ADD FOREIGN KEY ("term_termName") REFERENCES "term" ("termName");

ALTER TABLE "term_posting" ADD FOREIGN KEY ("posting_termName") REFERENCES "posting" ("termName");


ALTER TABLE "posting" ADD CONSTRAINT "fk_posting_file" FOREIGN KEY ("fileId") REFERENCES "file" ("id") ON DELETE CASCADE;

CREATE TABLE "invertedindex_term" (
  "invertedindex_termName" TEXT,
  "term_termName" TEXT,
  PRIMARY KEY ("invertedindex_termName", "term_termName")
);

ALTER TABLE "invertedindex_term" ADD FOREIGN KEY ("invertedindex_termName") REFERENCES "invertedindex" ("termName");

ALTER TABLE "invertedindex_term" ADD FOREIGN KEY ("term_termName") REFERENCES "term" ("termName");

