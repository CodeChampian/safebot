import * as React from "react"

// Simplified dialog components without Radix dependencies
const Dialog = ({ open, onOpenChange, children }) => {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50"
        onClick={() => onOpenChange(false)}
      />
      {/* Dialog content will be positioned by DialogContent */}
      {children}
    </div>
  );
};

const DialogTrigger = ({ asChild, children, ...props }) => {
  return React.cloneElement(children, props);
};

const DialogContent = ({ className, children, onClose, ...props }) => {
  const handleCloseClick = (e) => {
    e.stopPropagation();
    if (onClose) {
      onClose();
    }
  };

  return (
    <div className={`relative bg-white rounded-lg shadow-lg max-w-lg w-full mx-4 max-h-[90vh] overflow-auto ${className || ''}`} {...props}>
      <button
        className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-white transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-slate-950 focus:ring-offset-2 w-6 h-6 flex items-center justify-center text-black hover:bg-gray-200 z-10"
        onClick={handleCloseClick}
      >
        ✕
      </button>
      {children}
    </div>
  );
};

const DialogHeader = ({ className, ...props }) => (
  <div className={`flex flex-col space-y-1.5 p-6 pb-4 ${className || ''}`} {...props} />
);

const DialogTitle = ({ className, ...props }) => (
  <h2 className={`text-lg font-semibold leading-none tracking-tight ${className || ''}`} {...props} />
);

const DialogFooter = ({ className, ...props }) => (
  <div className={`flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2 p-6 pt-0 ${className || ''}`} {...props} />
);

export {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
};
