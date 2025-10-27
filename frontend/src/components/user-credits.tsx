import { CreditsProvider, useCredits } from '@/context/CreditsContext';

function Credits() {
  const { credits, tierData } = useCredits();

  return (
    <span>
      <strong className="text-primary">${credits}</strong>
      <br />
      {tierData?.tier_name} {tierData?.final_discount ? `(${tierData.final_discount * 100}% off)` : ''}
    </span>
  );
}

export default function UserCredits() {
  return (
    <CreditsProvider>
      <Credits />
    </CreditsProvider>
  );
}
