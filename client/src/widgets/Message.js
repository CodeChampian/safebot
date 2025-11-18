import React from 'react';
import { Avatar, AvatarFallback } from '@radix-ui/react-avatar';
import './Message.css';

const Message = ({ message }) => {
  const formatTime = (timestamp) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className={`message ${message.sender}-message ${message.isError ? 'error' : ''}`}>
      <div className="message-content">
        <div className="message-text">
          {message.text}
        </div>
        <div className="message-time">
          {formatTime(message.timestamp)}
        </div>
      </div>
      <Avatar className="message-avatar">
        <AvatarFallback>{message.sender === 'bot' ? '🤖' : '👤'}</AvatarFallback>
      </Avatar>
    </div>
  );
};

export default Message;
