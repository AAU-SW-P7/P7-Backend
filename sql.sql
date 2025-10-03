-- Drop tables if you're iterating (optional)
-- DROP TABLE IF EXISTS "posting","invertedindex","term","file","service","users" CASCADE;

CREATE TABLE "users" (
  "id" SERIAL PRIMARY KEY,
  "username" TEXT NOT NULL,
  "primaryProvider" TEXT NOT NULL
);

CREATE TABLE "service" (
  "id" SERIAL PRIMARY KEY,
  "userId" INTEGER NOT NULL,
  "oauthType" TEXT NOT NULL,
  "oauthToken" TEXT NOT NULL,
  "accessToken" TEXT NOT NULL,
  "accessTokenExpiration" TIMESTAMPTZ NOT NULL,
  "refreshToken" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "accountId" TEXT NOT NULL,
  "email" TEXT NOT NULL,
  "scopeName" TEXT NOT NULL,
  CONSTRAINT fk_service_user
    FOREIGN KEY ("userId") REFERENCES "users" ("id") ON DELETE CASCADE
);

CREATE TABLE "file" (
  "id" SERIAL PRIMARY KEY,
  "serviceId" INTEGER NOT NULL,
  "parent" INTEGER,                        -- make NULL allowed for roots
  "name" TEXT NOT NULL,
  "type" TEXT NOT NULL,
  "downloadable" BOOLEAN NOT NULL,
  "path" TEXT NOT NULL,
  "link" TEXT NOT NULL,
  "createdAt" TIMESTAMPTZ NOT NULL,
  "lastIndexed" TIMESTAMPTZ NOT NULL,
  "checksum" TEXT,
  "snippet" TEXT,
  CONSTRAINT fk_file_service
    FOREIGN KEY ("serviceId") REFERENCES "service" ("id") ON DELETE CASCADE,
  CONSTRAINT fk_file_parent
    FOREIGN KEY ("parent") REFERENCES "file" ("id") ON DELETE SET NULL
);

CREATE TABLE "term" (
  "id" SERIAL PRIMARY KEY,
  "termName" TEXT NOT NULL,
  "documentFrequency" INTEGER NOT NULL
);

CREATE TABLE "invertedindex" (
  "id" SERIAL PRIMARY KEY,
  "userId" INTEGER NOT NULL,
  "termId" INTEGER NOT NULL,
  CONSTRAINT fk_inv_user
    FOREIGN KEY ("userId") REFERENCES "users" ("id") ON DELETE CASCADE,
  CONSTRAINT fk_inv_term
    FOREIGN KEY ("termId") REFERENCES "term" ("id") ON DELETE CASCADE,
  CONSTRAINT uq_inv_user_term UNIQUE ("userId","termId")   -- helpful uniqueness
);

CREATE TABLE "posting" (
  "id" SERIAL PRIMARY KEY,
  "termId" INTEGER NOT NULL,
  "fileId" INTEGER NOT NULL,
  "termFrequency" INTEGER NOT NULL,
  CONSTRAINT fk_posting_term
    FOREIGN KEY ("termId") REFERENCES "term" ("id") ON DELETE CASCADE,
  CONSTRAINT fk_posting_file
    FOREIGN KEY ("fileId") REFERENCES "file" ("id") ON DELETE CASCADE
);