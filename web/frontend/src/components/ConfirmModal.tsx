import { useEffect, useId, useRef, type ReactNode } from 'react';
export function ConfirmModal({ open, title, children, onConfirm, onCancel, confirmLabel = 'Confirmar' }: { open: boolean; title: string; children: ReactNode; onConfirm: () => void; onCancel: () => void; confirmLabel?: string }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  useEffect(() => {
    const element = dialog.current;
    if (!element || !open) return;
    const previous = document.activeElement;
    element.showModal();
    return () => { element.close(); if (previous instanceof HTMLElement) previous.focus(); };
  }, [open]);
  return <dialog ref={dialog} aria-labelledby={titleId} onCancel={event => { event.preventDefault(); onCancel(); }} onClick={event => { if (event.target === event.currentTarget) onCancel(); }}><h2 id={titleId}>{title}</h2><div>{children}</div><div className="actions"><button className="secondary" onClick={onCancel} autoFocus>Cancelar</button><button onClick={onConfirm}>{confirmLabel}</button></div></dialog>;
}
