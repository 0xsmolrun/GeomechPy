// Pore Pressure Calculations
// Reference: Zhang, Jon Jincai. Applied petroleum geomechanics. Chapter 6.1

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
