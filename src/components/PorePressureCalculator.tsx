import { useState } from 'react';
import { Layers, Waves } from 'lucide-react';
import { calculatePorePressureOnshore, calculatePorePressureOffshore } from '../calculations/porePressure';
import { calculateOverburdenStressOnshore, calculateOverburdenStressOffshore } from '../calculations/overburdenStress';

export function PorePressureCalculator() {
  const [mode, setMode] = useState<'onshore' | 'offshore'>('onshore');
  const [tvd, setTvd] = useState<string>('10000');
  const [porePressureGradient, setPorePressureGradient] = useState<string>('0.47');
  const [airGap, setAirGap] = useState<string>('0');
  const [waterDepth, setWaterDepth] = useState<string>('0');
  const [seaWaterGradient, setSeaWaterGradient] = useState<string>('0.47');
  const [lithostaticGradient, setLithostaticGradient] = useState<string>('1.05');

  const tvdNum = parseFloat(tvd) || 0;
  const porePressureGradientNum = parseFloat(porePressureGradient) || 0.47;
  const airGapNum = parseFloat(airGap) || 0;
  const waterDepthNum = parseFloat(waterDepth) || 0;
  const seaWaterGradientNum = parseFloat(seaWaterGradient) || 0.47;
  const lithostaticGradientNum = parseFloat(lithostaticGradient) || 1.05;

  const porePressure = mode === 'onshore'
    ? calculatePorePressureOnshore(tvdNum, porePressureGradientNum, airGapNum)
    : calculatePorePressureOffshore(tvdNum, porePressureGradientNum, airGapNum, waterDepthNum, seaWaterGradientNum);

  const overburdenStress = mode === 'onshore'
    ? calculateOverburdenStressOnshore(tvdNum, lithostaticGradientNum, airGapNum)
    : calculateOverburdenStressOffshore(tvdNum, lithostaticGradientNum, airGapNum, waterDepthNum, seaWaterGradientNum);

  const effectiveStress = overburdenStress - porePressure;

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Layers className="w-5 h-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900">Pore Pressure & Overburden Stress Calculator</h2>
        </div>

        <div className="flex gap-4 mb-6">
          <button
            onClick={() => setMode('onshore')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              mode === 'onshore'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Onshore
          </button>
          <button
            onClick={() => setMode('offshore')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              mode === 'offshore'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Offshore
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <InputField
            label="TVD (ft)"
            value={tvd}
            onChange={setTvd}
            tooltip="True Vertical Depth from drill floor"
          />
          <InputField
            label="Pore Pressure Gradient (psi/ft)"
            value={porePressureGradient}
            onChange={setPorePressureGradient}
            tooltip="Formation pore pressure gradient"
          />
          <InputField
            label="Air Gap (ft)"
            value={airGap}
            onChange={setAirGap}
            tooltip="Distance from drill floor to ground/sea level"
          />
          {mode === 'offshore' && (
            <>
              <InputField
                label="Water Depth (ft)"
                value={waterDepth}
                onChange={setWaterDepth}
                tooltip="Water depth from sea level to seabed"
              />
              <InputField
                label="Sea Water Gradient (psi/ft)"
                value={seaWaterGradient}
                onChange={setSeaWaterGradient}
                tooltip="Seawater pressure gradient"
              />
            </>
          )}
          <InputField
            label="Lithostatic Gradient (psi/ft)"
            value={lithostaticGradient}
            onChange={setLithostaticGradient}
            tooltip="Overburden stress gradient"
          />
        </div>

        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <ResultCard
            title="Pore Pressure"
            value={porePressure.toFixed(1)}
            unit="psi"
            icon={<Waves className="w-5 h-5 text-blue-500" />}
          />
          <ResultCard
            title="Overburden Stress"
            value={overburdenStress.toFixed(1)}
            unit="psi"
            icon={<Mountain className="w-5 h-5 text-amber-500" />}
          />
          <ResultCard
            title="Effective Stress"
            value={effectiveStress.toFixed(1)}
            unit="psi"
            icon={<Zap className="w-5 h-5 text-green-500" />}
          />
        </div>
      </div>
    </div>
  );
}

import { Mountain, Zap } from 'lucide-react';

interface InputFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  tooltip?: string;
}

function InputField({ label, value, onChange, tooltip }: InputFieldProps) {
  return (
    <div className="space-y-1">
      <label className="block text-sm font-medium text-gray-700">
        {label}
        {tooltip && (
          <span className="ml-1 text-gray-400 cursor-help" title={tooltip}>?</span>
        )}
      </label>
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        step="any"
      />
    </div>
  );
}

interface ResultCardProps {
  title: string;
  value: string;
  unit: string;
  icon: React.ReactNode;
}

function ResultCard({ title, value, unit, icon }: ResultCardProps) {
  return (
    <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <span className="text-sm font-medium text-gray-600">{title}</span>
      </div>
      <div className="text-2xl font-bold text-gray-900">
        {value} <span className="text-sm font-normal text-gray-500">{unit}</span>
      </div>
    </div>
  );
}
