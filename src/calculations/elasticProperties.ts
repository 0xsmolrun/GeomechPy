// Elastic Properties Calculations
// Reference: https://en.wikipedia.org/wiki/Elastic_modulus

export interface ElasticProperties {
  bulkModulus: number;
  youngsModulus: number;
  lameParameter: number;
  shearModulus: number;
  poissonsRatio: number;
  pWaveModulus: number;
}

export function convertFromBulkAndYoungs(bulkModulus: number, youngsModulus: number): ElasticProperties {
  const lameParameter = (3 * bulkModulus * (3 * bulkModulus - youngsModulus)) / (9 * bulkModulus - youngsModulus);
  const shearModulus = (3 * bulkModulus * youngsModulus) / (9 * bulkModulus - youngsModulus);
  const poissonsRatio = (3 * bulkModulus - youngsModulus) / (6 * bulkModulus);
  const pWaveModulus = (3 * bulkModulus * (3 * bulkModulus + youngsModulus)) / (9 * bulkModulus - youngsModulus);

  return { bulkModulus, youngsModulus, lameParameter, shearModulus, poissonsRatio, pWaveModulus };
}

export function convertFromBulkAndLame(bulkModulus: number, lameParameter: number): ElasticProperties {
  const youngsModulus = (9 * bulkModulus * (bulkModulus - lameParameter)) / (3 * bulkModulus - lameParameter);
  const shearModulus = (3 * (bulkModulus - lameParameter)) / 2;
  const poissonsRatio = lameParameter / (3 * bulkModulus - lameParameter);
  const pWaveModulus = 3 * bulkModulus - 2 * lameParameter;

  return { bulkModulus, youngsModulus, lameParameter, shearModulus, poissonsRatio, pWaveModulus };
}

export function convertFromBulkAndShear(bulkModulus: number, shearModulus: number): ElasticProperties {
  const youngsModulus = (9 * bulkModulus * shearModulus) / (3 * bulkModulus + shearModulus);
  const lameParameter = bulkModulus - (2 * shearModulus) / 3;
  const poissonsRatio = (3 * bulkModulus - 2 * shearModulus) / (2 * (3 * bulkModulus + shearModulus));
  const pWaveModulus = bulkModulus + (4 * shearModulus) / 3;

  return { bulkModulus, youngsModulus, lameParameter, shearModulus, poissonsRatio, pWaveModulus };
}

export function convertFromBulkAndPoissons(bulkModulus: number, poissonsRatio: number): ElasticProperties {
  const youngsModulus = 3 * bulkModulus * (1 - 2 * poissonsRatio);
  const lameParameter = (3 * bulkModulus * poissonsRatio) / (1 + poissonsRatio);
  const shearModulus = (3 * bulkModulus * (1 - 2 * poissonsRatio)) / (2 * (1 + poissonsRatio));
  const pWaveModulus = (3 * bulkModulus * (1 - poissonsRatio)) / (1 + poissonsRatio);

  return { bulkModulus, youngsModulus, lameParameter, shearModulus, poissonsRatio, pWaveModulus };
}

export function convertFromYoungsAndPoissons(youngsModulus: number, poissonsRatio: number): ElasticProperties {
  const bulkModulus = youngsModulus / (3 * (1 - 2 * poissonsRatio));
  const lameParameter = (youngsModulus * poissonsRatio) / ((1 + poissonsRatio) * (1 - 2 * poissonsRatio));
  const shearModulus = youngsModulus / (2 * (1 + poissonsRatio));
  const pWaveModulus = (youngsModulus * (1 - poissonsRatio)) / ((1 + poissonsRatio) * (1 - 2 * poissonsRatio));

  return { bulkModulus, youngsModulus, lameParameter, shearModulus, poissonsRatio, pWaveModulus };
}

export function convertFromShearAndPWave(shearModulus: number, pWaveModulus: number): ElasticProperties {
  const bulkModulus = pWaveModulus - (4 / 3) * shearModulus;
  const youngsModulus = (shearModulus * (3 * pWaveModulus - 4 * shearModulus)) / (pWaveModulus - shearModulus);
  const lameParameter = pWaveModulus - 2 * shearModulus;
  const poissonsRatio = (pWaveModulus - 2 * shearModulus) / (2 * pWaveModulus - 2 * shearModulus);

  return { bulkModulus, youngsModulus, lameParameter, shearModulus, poissonsRatio, pWaveModulus };
}

export function convertFromVelocity(pWaveVelocity: number, sWaveVelocity: number, density: number): ElasticProperties {
  const shearModulus = density * sWaveVelocity ** 2;
  const pWaveModulus = density * pWaveVelocity ** 2;
  return convertFromShearAndPWave(shearModulus, pWaveModulus);
}

export function convertFromSlowness(pWaveSlowness: number, sWaveSlowness: number, density: number): ElasticProperties {
  const shearModulus = density * (304800 / sWaveSlowness) ** 2;
  const pWaveModulus = density * (304800 / pWaveSlowness) ** 2;
  return convertFromShearAndPWave(shearModulus, pWaveModulus);
}
