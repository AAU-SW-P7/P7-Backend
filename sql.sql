-- Users
CREATE TABLE "users" (
  "id" BIGSERIAL PRIMARY KEY
);

-- Term (termName is a natural key; keep as UNIQUE so FKs can reference it)
CREATE TABLE "term" (
  "termName" TEXT NOT NULL,
  CONSTRAINT "uq_term_name" UNIQUE ("termName")
);

-- Service
CREATE TABLE "service" (
  "id" BIGSERIAL PRIMARY KEY,
  "userId" BIGINT NOT NULL,
  "oauthType" TEXT NOT NULL,
  "oauthToken" TEXT NOT NULL,
  "accessToken" TEXT NOT NULL,
  "accessTokenExpiration" TIMESTAMPTZ NOT NULL,
  "refreshToken" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "accountId" TEXT NOT NULL,
  "email" TEXT NOT NULL,
  "scopeName" TEXT NOT NULL,
  CONSTRAINT "fk_service_user"
    FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE CASCADE
);

-- File
CREATE TABLE "file" (
  "id" BIGSERIAL PRIMARY KEY,
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
  "content" TEXT,
  CONSTRAINT "fk_file_service"
    FOREIGN KEY ("serviceId") REFERENCES "service"("id") ON DELETE CASCADE,
  CONSTRAINT "uq_service_file_id" UNIQUE ("serviceId", "serviceFileId")
);

-- Inverted Index (per-user term stats)
CREATE TABLE "invertedindex" (
  "userId" BIGINT NOT NULL,
  "termName" TEXT NOT NULL,
  "documentFrequency" BIGINT NOT NULL,
  CONSTRAINT "fk_inv_user"
    FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE CASCADE,
  CONSTRAINT "fk_term_name"
    FOREIGN KEY ("termName") REFERENCES "term"("termName") ON DELETE CASCADE,
  CONSTRAINT "uq_inv_user_term_name" UNIQUE ("userId", "termName")
);

-- Posting list (per-file term stats)
CREATE TABLE "posting" (
  "termName" TEXT NOT NULL,
  "fileId" BIGINT NOT NULL,
  "termFrequency" BIGINT NOT NULL,
  CONSTRAINT "fk_posting_term"
    FOREIGN KEY ("termName") REFERENCES "term"("termName") ON DELETE CASCADE,
  CONSTRAINT "fk_posting_file"
    FOREIGN KEY ("fileId") REFERENCES "file"("id") ON DELETE CASCADE,
  CONSTRAINT "uq_term_name_file_id" UNIQUE ("termName", "fileId")
);