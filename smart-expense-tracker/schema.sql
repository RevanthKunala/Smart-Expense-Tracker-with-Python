-- ============================================================
--  Smart Expense Tracker — Schema (MySQL 8)
--  Run once to set up or migrate the database.
--  Safe to re-run: uses IF NOT EXISTS / IF NOT EXISTS guards.
-- ============================================================

CREATE DATABASE IF NOT EXISTS smart_expense_tracker
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE smart_expense_tracker;

-- ── Categories (reference, seeded below) ─────────────────────
CREATE TABLE IF NOT EXISTS categories (
    id   INT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_categories_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Users ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id         INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    username   VARCHAR(50)     NOT NULL,
    email      VARCHAR(150)    NOT NULL,
    password   VARCHAR(255)    NOT NULL,
    role       ENUM('user','admin') NOT NULL DEFAULT 'user',
    created_at DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_users_username (username),
    UNIQUE KEY uq_users_email    (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Expenses ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS expenses (
    id          INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    user_id     INT UNSIGNED    NOT NULL,
    category_id INT UNSIGNED    NOT NULL,
    amount      DECIMAL(10, 2)  NOT NULL,
    description VARCHAR(255)    NOT NULL,
    date        DATE            NOT NULL,
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_expense_user     FOREIGN KEY (user_id)     REFERENCES users(id)      ON DELETE CASCADE,
    CONSTRAINT fk_expense_category FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT,
    INDEX idx_expense_user_date     (user_id, date),
    INDEX idx_expense_user_category (user_id, category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Budgets ───────────────────────────────────────────────────
-- category_id NULL = overall monthly budget
CREATE TABLE IF NOT EXISTS budgets (
    id          INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    user_id     INT UNSIGNED    NOT NULL,
    category_id INT UNSIGNED    NULL,
    month       CHAR(7)         NOT NULL COMMENT 'YYYY-MM',
    amount      DECIMAL(10, 2)  NOT NULL,
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_budget_user     FOREIGN KEY (user_id)     REFERENCES users(id)      ON DELETE CASCADE,
    CONSTRAINT fk_budget_category FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
    UNIQUE KEY uq_budget_user_cat_month (user_id, category_id, month)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Recurring Expenses ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS recurring_expenses (
    id          INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    user_id     INT UNSIGNED    NOT NULL,
    category_id INT UNSIGNED    NOT NULL,
    amount      DECIMAL(10, 2)  NOT NULL,
    description VARCHAR(255)    NOT NULL,
    day_of_month TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '1–28',
    active      TINYINT(1)      NOT NULL DEFAULT 1,
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_rec_user     FOREIGN KEY (user_id)     REFERENCES users(id)      ON DELETE CASCADE,
    CONSTRAINT fk_rec_category FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT,
    INDEX idx_rec_user_active (user_id, active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Seed categories ───────────────────────────────────────────
INSERT IGNORE INTO categories (name) VALUES
    ('Food'),
    ('Travel'),
    ('Shopping'),
    ('Bills'),
    ('Health'),
    ('Others');

-- ── Alter existing tables (safe migration guards) ────────────
-- Add role column if upgrading from initial schema
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS role ENUM('user','admin') NOT NULL DEFAULT 'user' AFTER password;
