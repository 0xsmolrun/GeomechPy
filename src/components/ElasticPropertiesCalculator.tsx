import { useState } from 'react';
import { Zap, ArrowRightLeft } from 'lucide-react';
import {
  convertFromBulkAndYoungs,
  convertFromBulkAndShear,
  convertFromBulkAndPoissons,
  convertFromYoungsAndPoissons,
  convertFromVelocity,
  convertFromSlowness,
  ElasticProperties
} from '../calculations/elasticProperties';

type ConversionMode = 'bulk-youngs' | 'bulk-shear' | 'bulk-poissons' | 'youngs-poissons' | 'velocity' | 'slowness';

export function ElasticPropertiesCalculator() {
  const [mode, setMode] = useState<ConversionMode>('youngs-poissons');
  const [input1, setInput1] = useState<string>('30');
  const [input2, setInput2] = useState<string>('0.25');
  const [density, setDensity] = useState<string>('2500');

  let result: ElasticProperties | null = null;
  let input1Label = '';
  let input2Label = '';
  let input1Unit = '';
  let input2Unit = '';

  const val1 = parseFloat(input1) || 0;
  const val2 = parseFloat(input2) || 0;
  const densityVal = parseFloat(density) || 2500;

  switch (mode) {
    case 'bulk-youngs':
      input1Label = 'Bulk Modulus';
      input2Label = "Young's Modulus";
      input1Unit = 'GPa';
      input2Unit = 'GPa';
      result = convertFromBulkAndYoungs(val1, val2);
      break;
    case 'bulk-shear':
      input1Label = 'Bulk Modulus';
      input2Label = 'Shear Modulus';
      input1Unit = 'GPa';
      input2Unit = 'GPa';
      result = convertFromBulkAndShear(val1, val2);
      break;
    case 'bulk-poissons':
      input1Label = 'Bulk Modulus';
      input2Label = "Poisson's Ratio";
      input1Unit = 'GPa';
      input2Unit = '';
      result = convertFromBulkAndPoissons(val1, val2);
      break;
    case 'youngs-poissons':
      input1Label = "Young's Modulus";
      input2Label = "Poisson's Ratio";
      input1Unit = 'GPa';
      input2Unit = '';
      result = convertFromYoungsAndPoissons(val1, val2);
      break;
    case 'velocity':
      input1Label = 'P-Wave Velocity';
      input2Label = 'S-Wave Velocity';
      input1Unit = 'm/s';
      input2Unit = 'm/s';
      result = convertFromVelocity(val1, val2, densityVal);
      break;
    case 'slowness':
      input1Label = 'P-Wave Slowness';
      input2Label = 'S-Wave Slowness';
      input1Unit = 'us/ft';
      input2Unit = 'us/ft';
      result = convertFromSlowness(val1, val2, densityVal);
      break;
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Zap className="w-5 h-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900">Elastic Properties Converter</h2>
        </div>

        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">Conversion Type</label>
          <div className="flex flex-wrap gap-2">
            {[
              { id: 'youngs-poissons', label: "Young's + Poisson's" },
              { id: 'bulk-youngs', label: 'Bulk + Youngs' },
              { id: 'bulk-shear', label: 'Bulk + Shear' },
              { id: 'bulk-poissons', label: "Bulk + Poisson's" },
              { id: 'velocity', label: 'P/S Velocity' },
              { id: 'slowness', label: 'P/S Slowness' },
            ].map((opt) => (
              <button
                key={opt.id}
                onClick={() => setMode(opt.id as ConversionMode)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  mode === opt.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-1">
            <label className="block text-sm font-medium text-gray-700">
              {input1Label} {input1Unit && `(${input1Unit})`}
            </label>
            <input
              type="number"
              value={input1}
              onChange={(e) => setInput1(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              step="any"
            />
          </div>
          <div className="space-y-1">
            <label className="block text-sm font-medium text-gray-700">
              {input2Label} {input2Unit && `(${input2Unit})`}
            </label>
            <input
              type="number"
              value={input2}
              onChange={(e) => setInput2(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              step="any"
            />
          </div>
          {(mode === 'velocity' || mode === 'slowness') && (
            <div className="space-y-1">
              <label className="block text-sm font-medium text-gray-700">Density (kg/m3)</label>
              <input
                type="number"
                value={density}
                onChange={(e) => setDensity(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                step="any"
              />
            </div>
          )}
        </div>

        {result && (
          <div className="mt-6">
            <div className="flex items-center justify-center mb-4">
              <ArrowRightLeft className="w-5 h-5 text-gray-400" />
            </div>
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-200">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Calculated Properties</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <PropertyItem label="Bulk Modulus" value={result.bulkModulus} />
                <PropertyItem label="Young's Modulus" value={result.youngsModulus} />
                <PropertyItem label="Lame Parameter" value={result.lameParameter} />
                <PropertyItem label="Shear Modulus" value={result.shearModulus} />
                <PropertyItem label="Poisson's Ratio" value={result.poissonsRatio} />
                <PropertyItem label="P-Wave Modulus" value={result.pWaveModulus} />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

interface PropertyItemProps {
  label: string;
  value: number;
}

function PropertyItem({ label, value }: PropertyItemProps) {
  const displayValue = Math.abs(value) > 1e6 ? (value / 1e9).toFixed(3) + ' GPa' : value.toFixed(3);
  return (
    <div className="bg-white rounded-lg p-3 border border-gray-200">
      <div className="text-xs text-gray-500">{label}</div>
      <div className="text-sm font-semibold text-gray-900">{displayValue}</div>
    </div>
  );
}
