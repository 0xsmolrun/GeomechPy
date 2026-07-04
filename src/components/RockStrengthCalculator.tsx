import { useState } from 'react';
import { Wrench, Hammer } from 'lucide-react';
import { convertYmeStaToUcsPlumb, convertUcsToTstr, convertFrictionAngleLal } from '../calculations/rockStrength';
import { dyn2staYmeBradford, dyn2staYmeNajib, dyn2staYmeFuller, dyn2staYmeMorales } from '../calculations/staticElasticProperties';

export function RockStrengthCalculator() {
  const [ymeDyn, setYmeDyn] = useState<string>('3');
  const [porosity, setPorosity] = useState<string>('0.20');
  const [dtco, setDtco] = useState<string>('80');
  const [tstrMultiplier, setTstrMultiplier] = useState<string>('0.15');
  const [correlation, setCorrelation] = useState<'bradford' | 'najib' | 'fuller' | 'morales'>('bradford');

  const ymeDynNum = parseFloat(ymeDyn) || 0;
  const porosityNum = parseFloat(porosity) || 0.2;
  const dtcoNum = parseFloat(dtco) || 80;
  const tstrMultiplierNum = parseFloat(tstrMultiplier) || 0.15;

  let ymeSta: number;
  let correlationName: string;
  switch (correlation) {
    case 'bradford':
      ymeSta = dyn2staYmeBradford(ymeDynNum);
      correlationName = 'Bradford (Turbiditic Sandstones)';
      break;
    case 'najib':
      ymeSta = dyn2staYmeNajib(ymeDynNum);
      correlationName = 'Najib (Carbonates)';
      break;
    case 'fuller':
      ymeSta = dyn2staYmeFuller(ymeDynNum);
      correlationName = 'Fuller (Sandstone/Shale)';
      break;
    case 'morales':
      ymeSta = dyn2staYmeMorales(ymeDynNum, porosityNum);
      correlationName = 'Morales (Sandstones)';
      break;
  }

  const ucs = convertYmeStaToUcsPlumb(ymeSta);
  const tstr = convertUcsToTstr(ucs, tstrMultiplierNum);
  const fang = convertFrictionAngleLal(dtcoNum);

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Wrench className="w-5 h-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900">Rock Strength Calculator</h2>
        </div>

        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">Young's Modulus Correlation</label>
          <div className="flex flex-wrap gap-2">
            {[
              { id: 'bradford', label: 'Bradford' },
              { id: 'najib', label: 'Najib' },
              { id: 'fuller', label: 'Fuller' },
              { id: 'morales', label: 'Morales' },
            ].map((opt) => (
              <button
                key={opt.id}
                onClick={() => setCorrelation(opt.id as typeof correlation)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  correlation === opt.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="space-y-1">
            <label className="block text-sm font-medium text-gray-700">Dynamic YME (Mpsi)</label>
            <input
              type="number"
              value={ymeDyn}
              onChange={(e) => setYmeDyn(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              step="any"
            />
          </div>
          {correlation === 'morales' && (
            <div className="space-y-1">
              <label className="block text-sm font-medium text-gray-700">Porosity (fraction)</label>
              <input
                type="number"
                value={porosity}
                onChange={(e) => setPorosity(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                step="0.01"
                min="0"
                max="1"
              />
            </div>
          )}
          <div className="space-y-1">
            <label className="block text-sm font-medium text-gray-700">Compressional Slowness (us/ft)</label>
            <input
              type="number"
              value={dtco}
              onChange={(e) => setDtco(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              step="any"
            />
          </div>
          <div className="space-y-1">
            <label className="block text-sm font-medium text-gray-700">TSTR Multiplier</label>
            <input
              type="number"
              value={tstrMultiplier}
              onChange={(e) => setTstrMultiplier(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              step="0.01"
            />
          </div>
        </div>

        <div className="mt-6">
          <div className="text-xs text-gray-500 mb-3">Correlation: {correlationName}</div>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <ResultBox label="Static YME" value={ymeSta.toFixed(3)} unit="Mpsi" />
            <ResultBox label="UCS" value={ucs.toFixed(1)} unit="psi" />
            <ResultBox label="Tensile Strength" value={tstr.toFixed(1)} unit="psi" />
            <ResultBox label="Friction Angle" value={fang.toFixed(1)} unit="deg" />
          </div>
        </div>

        <div className="mt-6 bg-gray-50 rounded-lg p-4 border border-gray-200">
          <h3 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
            <Hammer className="w-4 h-4" />
            All Correlations Comparison
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <ComparisonItem
              label="Bradford"
              value={dyn2staYmeBradford(ymeDynNum).toFixed(3)}
              unit="Mpsi"
            />
            <ComparisonItem
              label="Najib"
              value={dyn2staYmeNajib(ymeDynNum).toFixed(3)}
              unit="Mpsi"
            />
            <ComparisonItem
              label="Fuller"
              value={dyn2staYmeFuller(ymeDynNum).toFixed(3)}
              unit="GPa"
            />
            <ComparisonItem
              label="Morales"
              value={dyn2staYmeMorales(ymeDynNum, porosityNum).toFixed(3)}
              unit="Mpsi"
            />
          </div>
        </div>
      </div>
    </div>
  );
}

interface ResultBoxProps {
  label: string;
  value: string;
  unit: string;
}

function ResultBox({ label, value, unit }: ResultBoxProps) {
  return (
    <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
      <div className="text-xs text-gray-600">{label}</div>
      <div className="text-lg font-semibold text-gray-900">
        {value} <span className="text-xs font-normal text-gray-500">{unit}</span>
      </div>
    </div>
  );
}

interface ComparisonItemProps {
  label: string;
  value: string;
  unit: string;
}

function ComparisonItem({ label, value, unit }: ComparisonItemProps) {
  return (
    <div className="bg-white rounded p-2 border border-gray-200">
      <div className="text-xs text-gray-500">{label}</div>
      <div className="text-sm font-medium">{value} {unit}</div>
    </div>
  );
}
