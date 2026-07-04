// Horizontal Stress Calculations
// Reference: Zhang, Jon Jincai. Applied petroleum geomechanics. Chapter 6

export interface HorizontalStresses {
  shmin: number;
  shmax: number;
  qFactor: number;
  shmaxShminRatio: number;
}

export function calculatePoroelasticHorizontalStresses(
  overburdenStress: number,
  porePressure: number,
  poissonRatio: number,
  youngsModulus: number,
  biotCoefficient: number = 1.0,
  EX: number = 0.0001,
  EY: number = 0.009
): HorizontalStresses {
  const strainX = EX / 1e-3;
  const strainY = EY / 1e-3;
  const A = poissonRatio / (1 - poissonRatio);
  const B = youngsModulus / (1 - poissonRatio * poissonRatio);
  const C = (poissonRatio * youngsModulus) / (1 - poissonRatio * poissonRatio);

  const shmin = A * overburdenStress + (1 - A) * biotCoefficient * porePressure + B * strainX + C * strainY;
  const shmax = A * overburdenStress + (1 - A) * biotCoefficient * porePressure + B * strainY + C * strainX;

  const qFactor = calculateStressRegimeQFactor(0.0, shmax, shmin);
  const shmaxShminRatio = shmax / shmin;

  return { shmin, shmax, qFactor, shmaxShminRatio };
}

export function calculateShmaxMultiplier(shmin: number, shmaxMultiplier: number = 1.1): number {
  return shmin * shmaxMultiplier;
}

export function calculateStressRegimeQFactor(sigv: number, shmax: number, shmin: number): number {
  if (sigv > shmax && shmax >= shmin) {
    return (shmax - shmin) / (sigv - shmin);
  } else if (shmin < sigv && sigv <= shmax) {
    return 2 - (sigv - shmin) / (shmax - shmin);
  } else if (sigv <= shmin && shmin < shmax) {
    return 2 + (shmin - sigv) / (shmax - sigv);
  }
  return 4;
}

export function getStressRegimeLabel(qFactor: number): string {
  if (qFactor >= 0 && qFactor < 1) return "Normal Faulting";
  if (qFactor >= 1 && qFactor < 2) return "Strike-Slip";
  if (qFactor >= 2 && qFactor < 3) return "Reverse Faulting";
  return "Unclassified";
}
