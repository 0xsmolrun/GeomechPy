// Rock Strength Calculations
// Reference: Zhang, Yuliang, et al. "Extracting static elastic moduli of rock through elastic wave velocities." Acta Geophysica 72.2 (2024)

export function convertYmeStaToUcsPlumb(ymeSta: number): number {
  const multiplier = 0.210306770614015;
  return multiplier * ymeSta;
}

export function convertUcsToTstr(ucs: number, multiplier: number = 0.15): number {
  return multiplier * ucs;
}

export function convertFrictionAngleLal(dtco: number): number {
  const radians = Math.asin((304800 - 1000 * dtco) / (304800 + 1000 * dtco));
  return (180 / Math.PI) * radians;
}
