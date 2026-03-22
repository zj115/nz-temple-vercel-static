-- ═══════════════════════════════════════════════════════════
--  NZ Temple — Supabase 数据库初始化脚本
--  在 Supabase Dashboard → SQL Editor 中执行
-- ═══════════════════════════════════════════════════════════

-- ─────────────────────────────────────────────────────────
-- 1. 扩展 member_profiles 表（八字字段）
-- ─────────────────────────────────────────────────────────
ALTER TABLE member_profiles
  ADD COLUMN IF NOT EXISTS bazi_year          TEXT,
  ADD COLUMN IF NOT EXISTS bazi_month         TEXT,
  ADD COLUMN IF NOT EXISTS bazi_day           TEXT,
  ADD COLUMN IF NOT EXISTS bazi_hour          TEXT,
  ADD COLUMN IF NOT EXISTS bazi_input_method  TEXT,  -- 'A' or 'B'
  ADD COLUMN IF NOT EXISTS birth_datetime     TIMESTAMPTZ;

-- ─────────────────────────────────────────────────────────
-- 2. 法事预约表
-- ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ritual_bookings (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id          UUID REFERENCES auth.users(id),
  service_type     TEXT NOT NULL,         -- 'chaodu' | 'yuanbao'

  -- 亡者信息
  deceased_name    TEXT NOT NULL,
  deceased_time    DATE,
  address          TEXT NOT NULL,

  -- 元宝专用
  quantity         INT DEFAULT 1,

  -- 预约人信息
  contact_name     TEXT NOT NULL,
  contact_info     TEXT NOT NULL,
  notes            TEXT,

  -- 状态
  status           TEXT DEFAULT 'pending', -- pending/confirmed/completed/cancelled

  created_at       TIMESTAMPTZ DEFAULT now()
);

-- ─────────────────────────────────────────────────────────
-- 3. 元宝库存表
-- ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS yuanbao_inventory (
  id           SERIAL PRIMARY KEY,
  batch_name   TEXT DEFAULT '第一批',
  total        INT  DEFAULT 100,
  sold         INT  DEFAULT 0,
  is_active    BOOLEAN DEFAULT true,
  created_at   TIMESTAMPTZ DEFAULT now()
);

INSERT INTO yuanbao_inventory (batch_name, total, sold, is_active)
VALUES ('第一批', 100, 0, true)
ON CONFLICT DO NOTHING;

-- ─────────────────────────────────────────────────────────
-- 4. 站点设置表
-- ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS site_settings (
  key        TEXT PRIMARY KEY,
  value      TEXT NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now()
);

INSERT INTO site_settings (key, value) VALUES
  ('notify_email',  'jzc19980926@gmail.com'),
  ('bank_name',     'THE NZ TAOIST ASSOCIATION CHARITABLE TRU'),
  ('bank_account',  '06-0273-0844030-00')
ON CONFLICT (key) DO NOTHING;

-- ─────────────────────────────────────────────────────────
-- 5. RLS 策略
-- ─────────────────────────────────────────────────────────

-- ritual_bookings
ALTER TABLE ritual_bookings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users can insert own bookings"
  ON ritual_bookings FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "users can view own bookings"
  ON ritual_bookings FOR SELECT
  USING (auth.uid() = user_id);

-- Admin 可以读写所有预约（需要先在 member_profiles 设置 role = 'admin'）
CREATE POLICY "admin full access to bookings"
  ON ritual_bookings FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM member_profiles
      WHERE id = auth.uid() AND role = 'admin'
    )
  );

-- yuanbao_inventory
ALTER TABLE yuanbao_inventory ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anyone can read inventory"
  ON yuanbao_inventory FOR SELECT
  USING (true);

CREATE POLICY "admin can manage inventory"
  ON yuanbao_inventory FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM member_profiles
      WHERE id = auth.uid() AND role = 'admin'
    )
  );

-- site_settings
ALTER TABLE site_settings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "admin can manage settings"
  ON site_settings FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM member_profiles
      WHERE id = auth.uid() AND role = 'admin'
    )
  );

-- ─────────────────────────────────────────────────────────
-- 6. 元宝库存 RPC 函数（原子递增，防止并发超卖）
-- ─────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION increment_yuanbao_sold(p_qty INT)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  UPDATE yuanbao_inventory
  SET sold = sold + p_qty
  WHERE is_active = true;
END;
$$;
