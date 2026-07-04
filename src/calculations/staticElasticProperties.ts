// Static Elastic Properties Conversions
// Reference: Zhang, Yuliang, et al. Acta Geophysica 72.2 (2024): 915-931.

export function dyn2staYmeBradford(ymeDyn: number): number {
  const multiplier = 0.04794626440600849;
  const exponent = 2.7;
  return multiplier * ymeDyn ** exponent;
}

export function dyn2staYmeNajib(ymeDyn: number): number {
  const multiplier = 0.07277314417314575;
  const exponent = 1.96;
  return multiplier * ymeDyn ** exponent;
}

export function dyn2staYmeFuller(ymeDyn: number): number {
  const multiplier = 0.08143824177457351;
  const exponent = 1.632;
  return multiplier * ymeDyn ** exponent;
}

export function dyn2staYmeMorales(ymeDyn: number, porosity: number, excludeLowPor: boolean = true): number {
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

  if (porosity < 0.10 && excludeLowPor) {
    return -9999;
  }
  return multiplier * ymeDyn ** exponent;
}

export function dyn2staPoissonsRatio(prDyn: number, multiplier: number = 1.0): number {
  return prDyn * multiplier;
}
