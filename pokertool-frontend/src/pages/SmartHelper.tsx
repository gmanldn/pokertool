/**
 * SmartHelper - Real-time Poker Decision Assistant
 *
 * Sophisticated AI-powered poker assistant providing instant action recommendations,
 * strategic reasoning, micro-analytics, and conversational analysis.
 */
import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  CircularProgress,
  Avatar,
  Chip,
  Grid,
  Button,
  Alert
} from '@mui/material';
import { Send, Psychology, Person, Refresh } from '@mui/icons-material';
import axios from 'axios';
import { buildApiUrl } from '../config/api';
import { ActionRecommendationCard, PokerAction } from '../components/smarthelper/ActionRecommendationCard';
import { ReasoningPanel, DecisionFactor } from '../components/smarthelper/ReasoningPanel';
import { MicroChartsGrid } from '../components/smarthelper/MicroChartsGrid';
import { createEquityDataPoint } from '../components/smarthelper/EquityChart';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface Recommendation {
  action: PokerAction;
  amount?: number;
  gtoFrequencies: {
    fold?: number;
    check?: number;
    call?: number;
    bet?: number;
    raise?: number;
    all_in?: number;
  };
  strategicReasoning: string;
  confidence: number;
  factors: DecisionFactor[];
  netConfidence: number;
}

export const SmartHelper: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [isLoadingRecommendation, setIsLoadingRecommendation] = useState(false);
  const [recommendationError, setRecommendationError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await axios.post(buildApiUrl('/api/ai/chat'), {
        query: userMessage.content
      });

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.data.response || 'I apologize, but I could not generate a response.',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('AI chat error:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const loadDemoRecommendation = async () => {
    setIsLoadingRecommendation(true);
    setRecommendationError(null);

    try {
      const response = await axios.get(buildApiUrl('/api/smarthelper/demo'));
      setRecommendation(response.data);
    } catch (error) {
      console.error('Failed to load demo recommendation:', error);
      setRecommendationError('Failed to load recommendation. Click refresh to try again.');
    } finally {
      setIsLoadingRecommendation(false);
    }
  };

  // Load demo recommendation on mount
  useEffect(() => {
    loadDemoRecommendation();
  }, []);

  const suggestedQuestions = [
    'How should I play pocket aces?',
    'What are pot odds?',
    'Analyze my last session',
    'What is a continuation bet?'
  ];

  return (
    <Box sx={{ height: 'calc(100vh - 64px)', overflow: 'auto', p: 2 }}>
      {/* Header */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Psychology sx={{ fontSize: 40, color: 'primary.main' }} />
            <Box>
              <Typography variant="h5" fontWeight="bold">
                🧠 SmartHelper
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Your real-time poker decision assistant - instant recommendations, strategic analysis, and micro-analytics
              </Typography>
            </Box>
          </Box>
          <Button
            startIcon={<Refresh />}
            onClick={loadDemoRecommendation}
            disabled={isLoadingRecommendation}
            variant="outlined"
            size="small"
          >
            Refresh Demo
          </Button>
        </Box>
      </Paper>

      {/* Main Content Grid */}
      <Grid container spacing={2}>
        {/* Left Column - Recommendations & Analytics */}
        <Grid item xs={12} lg={6}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {/* Action Recommendation */}
            {recommendationError ? (
              <Alert severity="error" action={
                <Button size="small" onClick={loadDemoRecommendation}>
                  Retry
                </Button>
              }>
                {recommendationError}
              </Alert>
            ) : isLoadingRecommendation ? (
              <Paper sx={{ p: 4, textAlign: 'center' }}>
                <CircularProgress />
                <Typography variant="body2" color="textSecondary" sx={{ mt: 2 }}>
                  Loading recommendation...
                </Typography>
              </Paper>
            ) : recommendation ? (
              <>
                <ActionRecommendationCard
                  action={recommendation.action}
                  amount={recommendation.amount}
                  gtoFrequencies={recommendation.gtoFrequencies}
                  strategicReasoning={recommendation.strategicReasoning}
                  confidence={recommendation.confidence}
                  isUpdating={false}
                />

                <ReasoningPanel
                  factors={recommendation.factors}
                  netConfidence={recommendation.netConfidence}
                />

                <MicroChartsGrid
                  equityData={[
                    createEquityDataPoint('Preflop', 58),
                    createEquityDataPoint('Flop', 62),
                    createEquityDataPoint('Turn', 65)
                  ]}
                  currentEquity={65}
                  potSize={150}
                  betToCall={50}
                  impliedOdds={2.5}
                  positionStats={{
                    position: 'BTN',
                    vpip: 28,
                    pfr: 22,
                    aggression: 2.8,
                    winRate: 12.5,
                    handsPlayed: 450
                  }}
                  gtoComparison={{
                    vpip: 25,
                    pfr: 20,
                    aggression: 2.5
                  }}
                  opponentStats={{
                    name: 'Villain',
                    vpip: 35,
                    pfr: 18,
                    threebet: 8,
                    foldToCbet: 65,
                    foldToThreebet: 55,
                    aggression: 2.5,
                    handsPlayed: 320
                  }}
                />
              </>
            ) : null}
          </Box>
        </Grid>

        {/* Right Column - Chat Interface */}
        <Grid item xs={12} lg={6}>
          <Paper sx={{ height: 'calc(100vh - 200px)', display: 'flex', flexDirection: 'column' }}>
            {/* Chat Header */}
            <Box sx={{ p: 2, borderBottom: '1px solid rgba(0, 0, 0, 0.12)' }}>
              <Typography variant="h6" fontWeight="bold">
                💬 Strategy Chat
              </Typography>
              <Typography variant="caption" color="textSecondary">
                Ask questions about poker strategy, hand analysis, and more
              </Typography>

              {/* Suggested Questions */}
              {messages.length === 0 && (
                <Box sx={{ mt: 2, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {suggestedQuestions.map((question) => (
                    <Chip
                      key={question}
                      label={question}
                      onClick={() => setInput(question)}
                      sx={{ cursor: 'pointer' }}
                      size="small"
                    />
                  ))}
                </Box>
              )}
            </Box>

            {/* Messages Area */}
            <Box
              sx={{
                flexGrow: 1,
                overflow: 'auto',
                p: 2,
                backgroundColor: 'rgba(0, 0, 0, 0.02)'
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
                    color: 'text.secondary'
                  }}
                >
                  <Psychology sx={{ fontSize: 60, mb: 2, opacity: 0.3 }} />
                  <Typography variant="subtitle1" gutterBottom>
                    Strategy Chat Ready
                  </Typography>
                  <Typography variant="body2" textAlign="center">
                    Ask me anything about poker strategy!
                  </Typography>
                </Box>
              ) : (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {messages.map((message) => (
                    <Box
                      key={message.id}
                      sx={{
                        display: 'flex',
                        gap: 2,
                        alignItems: 'flex-start',
                        flexDirection: message.role === 'user' ? 'row-reverse' : 'row'
                      }}
                    >
                      <Avatar
                        sx={{
                          bgcolor: message.role === 'user' ? 'primary.main' : 'secondary.main',
                          width: 32,
                          height: 32
                        }}
                      >
                        {message.role === 'user' ? <Person fontSize="small" /> : <Psychology fontSize="small" />}
                      </Avatar>

                      <Paper
                        sx={{
                          p: 1.5,
                          maxWidth: '80%',
                          backgroundColor: message.role === 'user' ? 'primary.main' : 'background.paper',
                          color: message.role === 'user' ? 'primary.contrastText' : 'text.primary'
                        }}
                      >
                        <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                          {message.content}
                        </Typography>
                        <Typography
                          variant="caption"
                          sx={{
                            mt: 0.5,
                            display: 'block',
                            opacity: 0.7,
                            fontSize: '10px'
                          }}
                        >
                          {message.timestamp.toLocaleTimeString()}
                        </Typography>
                      </Paper>
                    </Box>
                  ))}

                  {isLoading && (
                    <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                      <Avatar sx={{ bgcolor: 'secondary.main', width: 32, height: 32 }}>
                        <Psychology fontSize="small" />
                      </Avatar>
                      <Paper sx={{ p: 1.5 }}>
                        <CircularProgress size={16} />
                        <Typography variant="body2" sx={{ ml: 1, display: 'inline' }}>
                          Thinking...
                        </Typography>
                      </Paper>
                    </Box>
                  )}

                  <div ref={messagesEndRef} />
                </Box>
              )}
            </Box>

            {/* Input Area */}
            <Box sx={{ p: 2, borderTop: '1px solid rgba(0, 0, 0, 0.12)' }}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField
                  fullWidth
                  multiline
                  maxRows={3}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask me anything about poker..."
                  disabled={isLoading}
                  variant="outlined"
                  size="small"
                />
                <IconButton
                  color="primary"
                  onClick={handleSend}
                  disabled={!input.trim() || isLoading}
                  sx={{
                    bgcolor: 'primary.main',
                    color: 'white',
                    '&:hover': {
                      bgcolor: 'primary.dark'
                    },
                    '&:disabled': {
                      bgcolor: 'action.disabledBackground'
                    }
                  }}
                >
                  <Send />
                </IconButton>
              </Box>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default SmartHelper;
