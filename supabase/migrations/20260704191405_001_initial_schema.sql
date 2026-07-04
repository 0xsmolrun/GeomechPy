/*
# Wellbore Stability Workflow Schema

1. New Tables
- `wells` - Master table for well information
  - `id` (uuid, primary key)
  - `name` (text, not null) - Well name
  - `location` (text) - Well location/field
  - `operator` (text) - Operator company
  - `tvd_reference` (float) - Reference true vertical depth
  - `water_depth` (float) - Water depth for offshore
  - `air_gap` (float) - Air gap/KB elevation
  - `offshore` (boolean) - Onshore/offshore flag
  - `status` (text) - Well status (planning/drilling/completed)
  - `user_id` (uuid, defaults to authenticated user)
  - `created_at`/`updated_at` (timestamps)

- `formations` - geological formations per well
  - `id` (uuid, primary key)
  - `well_id` (uuid, foreign key to wells)
  - `name` (text) - Formation name
  - `top_depth_tvd` (float) - Top depth TVD
  - `base_depth_tvd` (float) - Base depth TVD
  - `lithology` (text) - Rock type
  - `created_at` (timestamp)

- `well_parameters` - Computed parameters per formation
  - `id` (uuid, primary key)
  - `formation_id` (uuid, foreign key)
  - `tvd` (float) - Depth reference
  - `pore_pressure` (float) - Computed pore pressure
  - `overburden_stress` (float) - Computed overburden
  - `shmin` (float) - Minimum horizontal stress
  - `shmax` (float) - Maximum horizontal stress
  - `ucs` (float) - Unconfined compressive strength
  - `tstr` (float) - Tensile strength
  - `friction_angle` (float) - Internal friction angle
  - `youngs_modulus_static` (float) - Static YM
  - `poisson_ratio_static` (float) - Static PR
  - `breakdown_pressure` (float) - Fracture pressure
  - `breakout_pressure` (float) - Collapse pressure
  - `created_at` (timestamp)

- `workflow_sessions` - Track workflow progress
  - `id` (uuid, primary key)
  - `well_id` (uuid, foreign key)
  - `current_step` (integer) - Current workflow step (1-6)
  - `step_data` (jsonb) - Step-specific parameters
  - `completed` (boolean) - Completion flag
  - `created_at`/`updated_at` (timestamps)

2. Security
- Enable RLS on all tables.
- Owner-scoped CRUD for wells/formations/parameters.
- Users can only access their own data.
*/

CREATE TABLE IF NOT EXISTS wells (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  location text,
  operator text,
  tvd_reference float DEFAULT 10000,
  water_depth float DEFAULT 0,
  air_gap float DEFAULT 0,
  offshore boolean DEFAULT false,
  status text DEFAULT 'planning',
  user_id uuid NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE wells ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "select_own_wells" ON wells;
CREATE POLICY "select_own_wells" ON wells FOR SELECT
  TO authenticated USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "insert_own_wells" ON wells;
CREATE POLICY "insert_own_wells" ON wells FOR INSERT
  TO authenticated WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "update_own_wells" ON wells;
CREATE POLICY "update_own_wells" ON wells FOR UPDATE
  TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "delete_own_wells" ON wells;
CREATE POLICY "delete_own_wells" ON wells FOR DELETE
  TO authenticated USING (auth.uid() = user_id);

CREATE TABLE IF NOT EXISTS formations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  well_id uuid NOT NULL REFERENCES wells(id) ON DELETE CASCADE,
  name text NOT NULL,
  top_depth_tvd float NOT NULL,
  base_depth_tvd float NOT NULL,
  lithology text,
  density float DEFAULT 2500,
  porosity float DEFAULT 0.20,
  p_wave_velocity float DEFAULT 3000,
  s_wave_velocity float DEFAULT 2000,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE formations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "select_own_formations" ON formations;
CREATE POLICY "select_own_formations" ON formations FOR SELECT
  TO authenticated USING (
    EXISTS (SELECT 1 FROM wells WHERE wells.id = formations.well_id AND wells.user_id = auth.uid())
  );

DROP POLICY IF EXISTS "insert_own_formations" ON formations;
CREATE POLICY "insert_own_formations" ON formations FOR INSERT
  TO authenticated WITH CHECK (
    EXISTS (SELECT 1 FROM wells WHERE wells.id = formations.well_id AND wells.user_id = auth.uid())
  );

DROP POLICY IF EXISTS "update_own_formations" ON formations;
CREATE POLICY "update_own_formations" ON formations FOR UPDATE
  TO authenticated USING (
    EXISTS (SELECT 1 FROM wells WHERE wells.id = formations.well_id AND wells.user_id = auth.uid())
  ) WITH CHECK (
    EXISTS (SELECT 1 FROM wells WHERE wells.id = formations.well_id AND wells.user_id = auth.uid())
  );

DROP POLICY IF EXISTS "delete_own_formations" ON formations;
CREATE POLICY "delete_own_formations" ON formations FOR DELETE
  TO authenticated USING (
    EXISTS (SELECT 1 FROM wells WHERE wells.id = formations.well_id AND wells.user_id = auth.uid())
  );

CREATE TABLE IF NOT EXISTS well_parameters (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  formation_id uuid NOT NULL REFERENCES formations(id) ON DELETE CASCADE,
  tvd float NOT NULL,
  pore_pressure float,
  pore_pressure_gradient float DEFAULT 0.47,
  overburden_stress float,
  lithostatic_gradient float DEFAULT 1.05,
  shmin float,
  shmax float,
  q_factor float,
  ucs float,
  tstr float,
  friction_angle float,
  youngs_modulus_static float,
  poisson_ratio_static float,
  youngs_modulus_dynamic float,
  poisson_ratio_dynamic float,
  breakdown_pressure float,
  breakout_pressure float,
  safe_mud_window float,
  biot_coefficient float DEFAULT 1.0,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE well_parameters ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "select_own_parameters" ON well_parameters;
CREATE POLICY "select_own_parameters" ON well_parameters FOR SELECT
  TO authenticated USING (
    EXISTS (
      SELECT 1 FROM formations
      JOIN wells ON wells.id = formations.well_id
      WHERE formations.id = well_parameters.formation_id AND wells.user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "insert_own_parameters" ON well_parameters;
CREATE POLICY "insert_own_parameters" ON well_parameters FOR INSERT
  TO authenticated WITH CHECK (
    EXISTS (
      SELECT 1 FROM formations
      JOIN wells ON wells.id = formations.well_id
      WHERE formations.id = well_parameters.formation_id AND wells.user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "update_own_parameters" ON well_parameters;
CREATE POLICY "update_own_parameters" ON well_parameters FOR UPDATE
  TO authenticated USING (
    EXISTS (
      SELECT 1 FROM formations
      JOIN wells ON wells.id = formations.well_id
      WHERE formations.id = well_parameters.formation_id AND wells.user_id = auth.uid()
    )
  ) WITH CHECK (
    EXISTS (
      SELECT 1 FROM formations
      JOIN wells ON wells.id = formations.well_id
      WHERE formations.id = well_parameters.formation_id AND wells.user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "delete_own_parameters" ON well_parameters;
CREATE POLICY "delete_own_parameters" ON well_parameters FOR DELETE
  TO authenticated USING (
    EXISTS (
      SELECT 1 FROM formations
      JOIN wells ON wells.id = formations.well_id
      WHERE formations.id = well_parameters.formation_id AND wells.user_id = auth.uid()
    )
  );

CREATE TABLE IF NOT EXISTS workflow_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  well_id uuid NOT NULL REFERENCES wells(id) ON DELETE CASCADE,
  current_step integer DEFAULT 1,
  step_data jsonb DEFAULT '{}',
  completed boolean DEFAULT false,
  user_id uuid NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE workflow_sessions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "select_own_sessions" ON workflow_sessions;
CREATE POLICY "select_own_sessions" ON workflow_sessions FOR SELECT
  TO authenticated USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "insert_own_sessions" ON workflow_sessions;
CREATE POLICY "insert_own_sessions" ON workflow_sessions FOR INSERT
  TO authenticated WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "update_own_sessions" ON workflow_sessions;
CREATE POLICY "update_own_sessions" ON workflow_sessions FOR UPDATE
  TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "delete_own_sessions" ON workflow_sessions;
CREATE POLICY "delete_own_sessions" ON workflow_sessions FOR DELETE
  TO authenticated USING (auth.uid() = user_id);

-- Create indexes for frequently queried columns
CREATE INDEX IF NOT EXISTS idx_wells_user_id ON wells(user_id);
CREATE INDEX IF NOT EXISTS idx_formations_well_id ON formations(well_id);
CREATE INDEX IF NOT EXISTS idx_parameters_formation_id ON well_parameters(formation_id);
CREATE INDEX IF NOT EXISTS idx_sessions_well_id ON workflow_sessions(well_id);
