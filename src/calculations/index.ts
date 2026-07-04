// Pore Pressure Calculations
const AIR_GRADIENT = 0.0004; // psi/ft

export function calculatePorePressureOnshore(
  tvd: number,
  formationPorePressureGradient: number = 0.47,
  airGap: number = 0.0
): number {
  const airPressure = AIR_GRADIENT * airGap;
  if (tvd >= 0 && tvd < airGap) {
    return AIR_GRADIENT * tvd;
  }
  return airPressure + formationPorePressureGradient * (tvd - airGap);
}

export function calculatePorePressureOffshore(
  tvd: number,
  formationPorePressureGradient: number = 0.47,
  airGap: number = 0.0,
  waterDepth: number = 0.0,
  seaWaterPressureGradient: number = 0.47
): number {
  const airPressure = AIR_GRADIENT * airGap;
  const waterPressure = seaWaterPressureGradient * waterDepth;

  if (tvd >= 0 && tvd < airGap) {
    return AIR_GRADIENT * tvd;
  } else if (tvd >= airGap && tvd <= airGap + waterDepth) {
    return airPressure + seaWaterPressureGradient * (tvd - airGap);
  }
  return airPressure + waterPressure + formationPorePressureGradient * (tvd - waterDepth - airGap);
}

// Overburden Stress
export function calculateOverburdenStressOnshore(
  tvd: number,
  lithostaticGradient: number = 1.05,
  airGap: number = 0.0
): number {
  const airPressure = AIR_GRADIENT * airGap;
  if (tvd >= 0 && tvd < airGap) {
    return AIR_GRADIENT * tvd;
  }
  return airPressure + lithostaticGradient * (tvd - airGap);
}

export function calculateOverburdenStressOffshore(
  tvd: number,
  lithostaticGradient: number = 1.05,
  airGap: number = 0.0,
  waterDepth: number = 0.0,
  seaWaterPressureGradient: number = 0.47
): number {
  const airPressure = AIR_GRADIENT * airGap;
  const waterPressure = seaWaterPressureGradient * waterDepth;

  if (tvd >= 0 && tvd < airGap) {
    return AIR_GRADIENT * tvd;
  } else if (tvd >= airGap && tvd <= airGap + waterDepth) {
    return airPressure + seaWaterPressureGradient * (tvd - airGap);
  }
  return airPressure + waterPressure + lithostaticGradient * (tvd - waterDepth - airGap);
}

// Elastic Properties
export interface ElasticProperties {
  bulkModulus: number;
  youngsModulus: number;
  lameParameter: number;
  shearModulus: number;
  poissonsRatio: number;
  pWaveModulus: number;
}

export function calculateElasticFromVelocity(
  pWaveVelocity: number,
  sWaveVelocity: number,
  density: number
): ElasticProperties {
  const shearModulus = density * Math.pow(sWaveVelocity, 2);
  const pWaveModulus = density * Math.pow(pWaveVelocity, 2);
  const bulkModulus = pWaveModulus - (4 / 3) * shearModulus;
  const lameParameter = pWaveModulus - 2 * shearModulus;
  const youngsModulus = (shearModulus * (3 * pWaveModulus - 4 * shearModulus)) / (pWaveModulus - shearModulus);
  const poissonsRatio = (pWaveModulus - 2 * shearModulus) / (2 * pWaveModulus - 2 * shearModulus);
  return { bulkModulus, youngsModulus, lameParameter, shearModulus, poissonsRatio, pWaveModulus };
}

// Static Elastic Properties
export function dyn2staYmeBradford(ymeDyn: number): number {
  return 0.04794626440600849 * Math.pow(ymeDyn, 2.7);
}

export function dyn2staYmeNajib(ymeDyn: number): number {
  return 0.07277314417314575 * Math.pow(ymeDyn, 1.96);
}

export function dyn2staYmeMorales(ymeDyn: number, porosity: number): number {
  let multiplier: number;
  let exponent: number;
  if (porosity < 0.15) {
    multiplier = 2.562214651764409;
    exponent = 0.6612;
  } else if (porosity < 0.25) {
    multiplier = 0.5281242638335621;
    exponent = 0.6920;
  } else {
    multiplier = 0.3467028522374105;
    exponent = 0.9404;
  }
  if (porosity < 0.10) return -9999;
  return multiplier * Math.pow(ymeDyn, exponent);
}

// Rock Strength
export function convertYmeStaToUcsPlumb(ymeSta: number): number {
  return 0.210306770614015 * ymeSta;
}

export function convertUcsToTstr(ucs: number, multiplier: number = 0.15): number {
  return multiplier * ucs;
}

export function calculateFrictionAngle(dtco: number): number {
  const radians = Math.asin((304800 - 1000 * dtco) / (304800 + 1000 * dtco));
  return (180 / Math.PI) * radians;
}

// Horizontal Stresses
export interface HorizontalStresses {
  shmin: number;
  shmax: number;
  qFactor: number;
  stressRegime: string;
}

export function calculateHorizontalStresses(
  overburdenStress: number,
  porePressure: number,
  poissonRatio: number,
  youngsModulus: number,
  biotCoefficient: number = 1.0,
  tectonicStrainX: number = 0.1,
  tectonicStrainY: number = 9.0
): HorizontalStresses {
  const A = poissonRatio / (1 - poissonRatio);
  const B = youngsModulus / (1 - poissonRatio * poissonRatio);
  const C = (poissonRatio * youngsModulus) / (1 - poissonRatio * poissonRatio);

  const shmin = A * overburdenStress + (1 - A) * biotCoefficient * porePressure + B * tectonicStrainX + C * tectonicStrainY;
  const shmax = A * overburdenStress + (1 - A) * biotCoefficient * porePressure + B * tectonicStrainY + C * tectonicStrainX;

  let qFactor: number;
  let stressRegime: string;

  if (overburdenStress > shmax && shmax >= shmin) {
    qFactor = (shmax - shmin) / (overburdenStress - shmin);
    stressRegime = 'Normal Faulting';
  } else if (shmin < overburdenStress && overburdenStress <= shmax) {
    qFactor = 2 - (overburdenStress - shmin) / (shmax - shmin);
    stressRegime = 'Strike-Slip';
  } else if (overburdenStress <= shmin && shmin < shmax) {
    qFactor = 2 + (shmin - overburdenStress) / (shmax - overburdenStress);
    stressRegime = 'Reverse Faulting';
  } else {
    qFactor = 4;
    stressRegime = 'Unclassified';
  }

  return { shmin, shmax, qFactor, stressRegime };
}

// Wellbore Stability
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
  frictionAngle: number,
  poissonRatio: number
): number {
  const q = Math.pow(Math.tan((45 + frictionAngle / 2) * (Math.PI / 180)), 2);
  const CC = ucs - porePressure * (q - 1);
  const A = 3 * shmax - shmin;
  const B = overburdenStress + 2 * poissonRatio * (shmax - shmin);

  const Pw_z_t_r = (B - CC) / q;
  const Pw_t_z_r = (A - CC) / (1 + q);
  const Pw_t_r_z = A - CC - q * B;

  return Math.max(Pw_z_t_r, Pw_t_z_r, Pw_t_r_z);
}

// Utility functions
export function mudWeightToPpg(pressurePsi: number, tvdFt: number): number {
  return pressurePsi / (0.052 * tvdFt);
}

export function ppgToMudWeight(ppg: number, tvdFt: number): number {
  return ppg * 0.052 * tvdFt;
}
