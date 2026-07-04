// Overburden Stress Calculations
// Reference: Zhang, Jon Jincai. Applied petroleum geomechanics. Chapter 6.1

const AIR_GRADIENT = 0.0004; // psi/ft

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
