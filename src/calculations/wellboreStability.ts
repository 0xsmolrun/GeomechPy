// Wellbore Stability Calculations
// Reference: Jaeger, John Conrad, et al. Fundamentals of rock mechanics.

export function calculateBreakdownPressure(
  shmax: number,
  shmin: number,
  porePressure: number,
  tstr: number
): number {
  return 3 * shmin - shmax - porePressure + tstr;
}

export function calculateBreakoutPressure(
  shmax: number,
  shmin: number,
  porePressure: number,
  overburdenStress: number,
  ucs: number,
  fang: number,
  prSta: number
): number {
  const q = Math.tan((45 + fang / 2) * (Math.PI / 180)) ** 2;
  const CC = ucs - porePressure * (q - 1);

  const A = 3 * shmax - shmin;
  const B = overburdenStress + 2 * prSta * (shmax - shmin);

  const Pw_z_t_r = (B - CC) / q;
  const Pw_t_z_r = (A - CC) / (1 + q);
  const Pw_t_r_z = A - CC - q * B;

  return Math.max(Pw_z_t_r, Pw_t_z_r, Pw_t_r_z);
}

export interface MudWindow {
  breakdown: number;
  breakout: number;
  safeWindow: number;
}
