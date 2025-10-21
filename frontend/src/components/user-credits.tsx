import { CreditsProvider, useCredits } from '@/context/CreditsContext';

function Credits() {
  const { credits } = useCredits();

  return (
    <span>
      <strong className="text-primary">${credits}</strong>
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
