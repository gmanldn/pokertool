import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  IconButton,
  List,
  ListItem,
  Avatar,
  Chip,
  CircularProgress,
  Alert,
  Tooltip,
  Divider,
} from '@mui/material';
import {
  Send as SendIcon,
  SmartToy as AIIcon,
  Person as PersonIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import axios from 'axios';
import { buildApiUrl } from '../config/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const AIChat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Load chat history from localStorage
  useEffect(() => {
    const savedMessages = localStorage.getItem('ai_chat_history');
    if (savedMessages) {
      try {
        const parsed = JSON.parse(savedMessages);
        setMessages(
          parsed.map((msg: Message) => ({
            ...msg,
            timestamp: new Date(msg.timestamp),
          }))
        );
      } catch (e) {
        console.error('Failed to parse saved messages:', e);
      }
    }
  }, []);

  // Save chat history to localStorage
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem('ai_chat_history', JSON.stringify(messages));
    }
  }, [messages]);

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setError(null);

    try {
      const response = await axios.post(
        buildApiUrl('/api/ai/chat'),
        {
          query: userMessage.content,
          chat_history: messages.map((msg) => ({
            role: msg.role,
            content: msg.content,
          })),
        },
        {
          timeout: 30000, // 30 second timeout
        }
      );

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.data.response || 'No response received.',
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Failed to send message:', err);
      let errorMessage = 'Failed to get response from AI. Please try again.';
      
      if (axios.isAxiosError(err)) {
        if (err.code === 'ECONNABORTED') {
          errorMessage = 'Request timed out. Please try again.';
        } else if (err.response) {
          errorMessage = `Error: ${err.response.status} - ${err.response.statusText}`;
        } else if (err.request) {
          errorMessage = 'No response from server. Please check your connection.';
        }
      }
      
      setError(errorMessage);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleClearChat = () => {
    if (window.confirm('Are you sure you want to clear the chat history?')) {
      setMessages([]);
      localStorage.removeItem('ai_chat_history');
      setError(null);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    localStorage.removeItem('ai_chat_history');
    setError(null);
    inputRef.current?.focus();
  };

  return (
    <Box
      sx={{
        height: 'calc(100vh - 64px)',
        display: 'flex',
        flexDirection: 'column',
        p: 2,
        bgcolor: 'background.default',
      }}
    >
      {/* Header */}
      <Paper
        elevation={2}
        sx={{
          p: 2,
          mb: 2,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <AIIcon sx={{ fontSize: 40, color: 'primary.main' }} />
          <Box>
            <Typography variant="h5" fontWeight="bold">
              AI Poker Coach
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Ask questions about strategy, hand analysis, and poker theory
            </Typography>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="New Chat">
            <IconButton onClick={handleNewChat} color="primary">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Clear History">
            <IconButton onClick={handleClearChat} color="error">
              <DeleteIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Paper>

      {/* Info Alert */}
      {messages.length === 0 && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <Typography variant="body2">
            <strong>Welcome!</strong> Ask me anything about poker strategy, hand analysis, opponent
            profiling, or review your recent hands. I have access to your hand history and can
            provide personalized advice.
          </Typography>
        </Alert>
      )}

      {/* Error Alert */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Messages Container */}
      <Paper
        elevation={2}
        sx={{
          flexGrow: 1,
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          bgcolor: 'background.paper',
        }}
      >
        <List
          sx={{
            flexGrow: 1,
            overflow: 'auto',
            p: 2,
            display: 'flex',
            flexDirection: 'column',
            gap: 2,
          }}
        >
          {messages.length === 0 ? (
            <Box
              sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                gap: 2,
                color: 'text.secondary',
              }}
            >
              <AIIcon sx={{ fontSize: 80, opacity: 0.3 }} />
              <Typography variant="h6">Start a conversation</Typography>
              <Typography variant="body2" textAlign="center" maxWidth={400}>
                Try asking:
                <br />
                "How should I play AK from early position?"
                <br />
                "Analyze my last session"
                <br />
                "What are common leaks in my game?"
              </Typography>
            </Box>
          ) : (
            messages.map((message) => (
              <ListItem
                key={message.id}
                sx={{
                  display: 'flex',
                  gap: 2,
                  alignItems: 'flex-start',
                  p: 0,
                }}
              >
                <Avatar
                  sx={{
                    bgcolor: message.role === 'user' ? 'primary.main' : 'secondary.main',
                    mt: 0.5,
                  }}
                >
                  {message.role === 'user' ? <PersonIcon /> : <AIIcon />}
                </Avatar>

                <Box sx={{ flexGrow: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                    <Typography variant="subtitle2" fontWeight="bold">
                      {message.role === 'user' ? 'You' : 'AI Coach'}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {message.timestamp.toLocaleTimeString()}
                    </Typography>
                  </Box>

                  <Paper
                    elevation={0}
                    sx={{
                      p: 2,
                      bgcolor:
                        message.role === 'user'
                          ? 'primary.main'
                          : 'background.default',
                      color: message.role === 'user' ? 'primary.contrastText' : 'text.primary',
                      borderRadius: 2,
                    }}
                  >
                    <Typography
                      variant="body1"
                      sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}
                    >
                      {message.content}
                    </Typography>
                  </Paper>
                </Box>
              </ListItem>
            ))
          )}

          {isLoading && (
            <ListItem
              sx={{
                display: 'flex',
                gap: 2,
                alignItems: 'flex-start',
                p: 0,
              }}
            >
              <Avatar sx={{ bgcolor: 'secondary.main', mt: 0.5 }}>
                <AIIcon />
              </Avatar>

              <Box sx={{ flexGrow: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                  <Typography variant="subtitle2" fontWeight="bold">
                    AI Coach
                  </Typography>
                  <Chip label="Thinking..." size="small" color="secondary" />
                </Box>

                <Paper
                  elevation={0}
                  sx={{
                    p: 2,
                    bgcolor: 'background.default',
                    borderRadius: 2,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 2,
                  }}
                >
                  <CircularProgress size={20} />
                  <Typography variant="body2" color="text.secondary">
                    Analyzing your question...
                  </Typography>
                </Paper>
              </Box>
            </ListItem>
          )}

          <div ref={messagesEndRef} />
        </List>

        <Divider />

        {/* Input Area */}
        <Box
          sx={{
            p: 2,
            display: 'flex',
            gap: 1,
            bgcolor: 'background.default',
          }}
        >
          <TextField
            inputRef={inputRef}
            fullWidth
            multiline
            maxRows={4}
            placeholder="Ask me anything about poker strategy..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isLoading}
            variant="outlined"
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 3,
              },
            }}
          />
          <Tooltip title="Send (Enter)">
            <span>
              <IconButton
                color="primary"
                onClick={handleSendMessage}
                disabled={!input.trim() || isLoading}
                sx={{
                  bgcolor: 'primary.main',
                  color: 'white',
                  '&:hover': {
                    bgcolor: 'primary.dark',
                  },
                  '&:disabled': {
                    bgcolor: 'action.disabledBackground',
                  },
                }}
              >
                <SendIcon />
              </IconButton>
            </span>
          </Tooltip>
        </Box>
      </Paper>

      {/* Footer */}
      <Typography
        variant="caption"
        color="text.secondary"
        sx={{ mt: 2, textAlign: 'center' }}
      >
        💡 Tip: The AI has access to your hand history and can provide personalized strategy
        advice based on your actual play.
      </Typography>
    </Box>
  );
};

export default AIChat;
