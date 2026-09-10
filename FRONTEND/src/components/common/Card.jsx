import React from 'react';

const Card = ({
  children,
  className = '',
  onClick,
  hoverable = false,
  bordered = true,
}) => {
  return (
    <div
      onClick={onClick}
      className={`bg-white rounded-xl ${
        bordered ? 'border border-slate-200/90' : ''
      } ${
        hoverable
          ? 'cursor-pointer transition-all duration-200 hover:border-slate-300 hover:shadow-sm'
          : 'shadow-subtle'
      } ${className}`}
    >
      {children}
    </div>
  );
};

export default Card;
