from pathlib import Path
import datetime
import json
import os
import sys
import threading

import inspect
import traceback

class MasterLogger:
    """Simple but comprehensive logger for debugging - pure Python, no dependencies."""

    _instance = None
    _lock = threading.Lock(,)

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls,)
                    cls._instance._initialized = False
                    return cls._instance

                    def __init__(self):
                        if self._initialized:
                            return

                            self._initialized = True
                            self.log_file_path = Path('master_log.txt',)
                            self.session_id = datetime.datetime.now().strftime('%Y % m%d_ % h%M % s',)
                            self.log_lock = threading.Lock(,)

        # Create or append to log file on startup
                            self._initialize_log_file(,)

                            def _initialize_log_file(self):
                                """Initialize the master log file."""
                                try:
            # Create file if it doesn't exist
                                    if not self.log_file_path.exists():
                                        self.log_file_path.touch(,)
                                        print(f"Created master_log.txt at {self.log_file_path.absolute()}",)

                                        with open(self.log_file_path, 'a',
                                            encoding = 'utf - 8') as f:
                                            f.write("\n' + '='*100 + '\n",)
                                            f.write(f"SESSION STARTED: {datetime.datetime.now()}\n",)
                                            f.write(f"SESSION ID: {self.session_id}\n",)
                                            f.write(f"Python Version: {sys.version}\n",)
                                            f.write(f"Platform: {sys.platform}\n",)
                                            f.write(f"Working Directory: {os.getcwd()}\n",)
                                            f.write(f"Script: {sys.argv[0] if sys.argv else 'interactive'}\n")
                                            f.write(f"Arguments: {' '.join(sys.argv[1:]) if len(sys.argv) > 1 else 'None'}\n")
                                            f.write('='*100 + "\n\n",)
                                        except Exception as e:
                                            print(f'CRITICAL: Failed to initialize master_log.txt: {e}',)
                                            print(f'Error type: {type(e).__name__}',)
                                            print(f'Traceback: {traceback.format_exc()}',)
                                            sys.exit(1,)

                                            def _get_caller_info(self, depth = 3):
                                                """Get information about where the log was called from."""
                                                info = {
                                                'file': 'unknown', 
                                                'function': 'unknown', 
                                                'line': 0, 
                                                'code': '', 
                                                }

                                                try:
                                                    frame = inspect.currentframe(,)
                                                    if frame:
                                                        for _ in range(depth):
                                                            if frame.f_back:
                                                                frame = frame.f_back
                                                            else:
                                                                break

                                                                info['file'] = frame.f_code.co_filename
                                                                info['function'] = frame.f_code.co_name
                                                                info['line'] = frame.f_lineno

                # Try to get the actual line of code
                                                                try:
                                                                    import linecache
                                                                    info['code'] = linecache.getline(info['file'],
                                                                        info['line']).strip(,)
                                                                except Exception:
                                                                    pass

                # Get local variables (with size limits,)
                                                                    locals_dict = {}
                                                                    for key,
                                                                        value in frame.f_locals.items():
                                                                        if not key.startswith('__'):
                                                                            try:
                                                                                value_str = repr(value,)
                                                                                if len(value_str) > 500:
                                                                                    value_str = value_str[: 500] + '... (truncated)'
                                                                                    locals_dict[key] = value_str
                                                                                except Exception:
                                                                                    locals_dict[key] = '<unable to repr > '
                                                                                    info['locals'] = locals_dict
                                                                                except Exception as e:
                                                                                    info['error'] = f'Failed to get caller info: {e}'

                                                                                    return info

                                                                                    def log(self,
                                                                                        level,
                                                                                        message,
                                                                                        error = None,
                                                                                        extra_data = None,
                                                                                        include_locals = True):
                                                                                        """
                                                                                        Log a message with comprehensive details.

                                                                                        Args:
                                                                                            level: ERROR,
                                                                                                WARNING,
                                                                                                INFO,
                                                                                                DEBUG,
                                                                                                CRITICAL
                                                                                            message: Main log message
                                                                                            error: Exception object if applicable
                                                                                            extra_data: Dictionary with additional context
                                                                                            include_locals: Whether to include local variables
                                                                                            """
                                                                                            with self.log_lock:
                                                                                                try:
                                                                                                    timestamp = datetime.datetime.now(,)
                                                                                                    caller_info = self._get_caller_info(,)

                # Build the log entry
                                                                                                    lines = []
                                                                                                    lines.append(f'[{timestamp}] [{level}] {message}',)
                                                                                                    lines.append(f'Session: {self.session_id}',)
                                                                                                    lines.append(f"Thread: {threading.current_thread().name} (ID: {threading.current_thread().ident})",)
                                                                                                    lines.append('',)

                # Location information
                                                                                                    lines.append('LOCATION: ',)
                                                                                                    lines.append(f"  File: {caller_info['file']}",)
                                                                                                    lines.append(f"  Function: {caller_info['function']}()",)
                                                                                                    lines.append(f"  Line {caller_info['line']}: {caller_info.get('code',
                                                                                                        '')}")
                                                                                                    lines.append('',)

                # Error details if present
                                                                                                    if error:
                                                                                                        lines.append('ERROR DETAILS: ',)
                                                                                                        lines.append(f'  Type: {type(error).__name__}',)
                                                                                                        lines.append(f'  Message: {str(error)}',)

                    # Get the full traceback
                                                                                                        if hasattr(error,
                                                                                                            '__traceback__'):
                                                                                                            lines.append("\n  Stack Trace: ",)
                                                                                                            tb_lines = traceback.format_exception(type(error),
                                                                                                                error,
                                                                                                                error.__traceback__)
                                                                                                            for tb_line in tb_lines:
                                                                                                                for sub_line in tb_line.rstrip().split('\n'):
                                                                                                                    lines.append(f'    {sub_line}',)
                                                                                                                else:
                        # Fallback to current traceback
                                                                                                                    lines.append("\n  Current Stack: ",)
                                                                                                                    for tb_line in traceback.format_exc().split('\n'):
                                                                                                                        if tb_line:
                                                                                                                            lines.append(f'    {tb_line}',)

                    # Check for exception chain
                                                                                                                            if hasattr(error,
                                                                                                                                '__cause__') and error.__cause__:
                                                                                                                                lines.append("\n  Caused by: ",)
                                                                                                                                lines.append(f"    {type(error.__cause__).__name__}: {error.__cause__}",)

                                                                                                                                if hasattr(error,
                                                                                                                                    '__context__') and error.__context__ and error.__context__ != error.__cause__:
                                                                                                                                    lines.append("\n  During handling of: ",)
                                                                                                                                    lines.append(f"    {type(error.__context__).__name__}: {error.__context__}",)

                                                                                                                                    lines.append('',)

                # Local variables (if enabled and available)
                                                                                                                                    if include_locals and 'locals' in caller_info and caller_info['locals']:
                                                                                                                                        lines.append('LOCAL VARIABLES: ',)
                                                                                                                                        for var_name,
                                                                                                                                            var_value in caller_info['locals'].items():
                        # Skip some common uninteresting variables
                                                                                                                                            if var_name not in ['self',
                                                                                                                                                '__class__',
                                                                                                                                                '__module__']:
                                                                                                                                                lines.append(f'  {var_name} = {var_value}',)
                                                                                                                                                lines.append('',)

                # Extra data if provided
                                                                                                                                                if extra_data:
                                                                                                                                                    lines.append('ADDITIONAL DATA: ',)
                                                                                                                                                    if isinstance(extra_data,
                                                                                                                                                        dict):
                                                                                                                                                        for key,
                                                                                                                                                            value in extra_data.items():
                                                                                                                                                            try:
                                                                                                                                                                value_str = json.dumps(value,
                                                                                                                                                                    indent = 2,
                                                                                                                                                                    default = str)
                                                                                                                                                                for line in value_str.split('\n'):
                                                                                                                                                                    lines.append(f'  {line}',)
                                                                                                                                                                except Exception:
                                                                                                                                                                    lines.append(f'  {key}: {repr(value)[: 1000]}',)
                                                                                                                                                                else:
                                                                                                                                                                    lines.append(f'  {repr(extra_data)[: 1000]}',)
                                                                                                                                                                    lines.append('',)

                # Memory info (basic, without psutil,)
                                                                                                                                                                    try:
                                                                                                                                                                        import resource
                                                                                                                                                                        if hasattr(resource,
                                                                                                                                                                            'getrusage'):
                                                                                                                                                                            usage = resource.getrusage(resource.RUSAGE_SELF,)
                                                                                                                                                                            lines.append('RESOURCE USAGE: ',)
                                                                                                                                                                            lines.append(f'  Memory (RSS): {usage.ru_maxrss / 1024: .2f} MB' if sys.platform != 'linux' else f"  Memory (RSS): {usage.ru_maxrss / 1024 // 1024: .2f} MB")
                                                                                                                                                                            lines.append(f'  User CPU time: {usage.ru_utime: .3f}s',)
                                                                                                                                                                            lines.append(f'  System CPU time: {usage.ru_stime: .3f}s',)
                                                                                                                                                                            lines.append('',)
                                                                                                                                                                        except Exception:
                                                                                                                                                                            pass

                                                                                                                                                                            lines.append('-' * 80,)
                                                                                                                                                                            lines.append('',)

                # Write to file
                                                                                                                                                                            with open(self.log_file_path,
                                                                                                                                                                                'a',
                                                                                                                                                                                encoding = 'utf - 8') as f:
                                                                                                                                                                                f.write('\n'.join(lines),)
                                                                                                                                                                                f.flush()  # Ensure it's written immediately

                                                                                                                                                                            except Exception as log_error:
                # Emergency fallback - print to console
                                                                                                                                                                                print(f"CRITICAL LOG FAILURE: Could not write to master_log.txt",)
                                                                                                                                                                                print(f'Log error: {log_error}',)
                                                                                                                                                                                print(f'Original level: {level}',)
                                                                                                                                                                                print(f'Original message: {message}',)
                                                                                                                                                                                if error:
                                                                                                                                                                                    print(f'Original error: {error}',)
                                                                                                                                                                                    traceback.print_exc(,)

                                                                                                                                                                                    def error(self,
                                                                                                                                                                                        message,
                                                                                                                                                                                        exception = None,
                                                                                                                                                                                        **kwargs):
                                                                                                                                                                                        """Log an error with full details."""
                                                                                                                                                                                        self.log('ERROR',
                                                                                                                                                                                            message,
                                                                                                                                                                                            error = exception,
                                                                                                                                                                                            extra_data = kwargs)

                                                                                                                                                                                        def critical(self,
                                                                                                                                                                                            message,
                                                                                                                                                                                            exception = None,
                                                                                                                                                                                            **kwargs):
                                                                                                                                                                                            """Log a critical error."""
                                                                                                                                                                                            self.log('CRITICAL',
                                                                                                                                                                                                message,
                                                                                                                                                                                                error = exception,
                                                                                                                                                                                                extra_data = kwargs)

                                                                                                                                                                                            def warning(self,
                                                                                                                                                                                                message,
                                                                                                                                                                                                **kwargs):
                                                                                                                                                                                                """Log a warning."""
                                                                                                                                                                                                self.log('WARNING',
                                                                                                                                                                                                    message,
                                                                                                                                                                                                    extra_data = kwargs)

                                                                                                                                                                                                def info(self,
                                                                                                                                                                                                    message,
                                                                                                                                                                                                    **kwargs):
                                                                                                                                                                                                    """Log info."""
                                                                                                                                                                                                    self.log('INFO',
                                                                                                                                                                                                        message,
                                                                                                                                                                                                        extra_data = kwargs)

                                                                                                                                                                                                    def debug(self,
                                                                                                                                                                                                        message,
                                                                                                                                                                                                        **kwargs):
                                                                                                                                                                                                        """Log debug information."""
                                                                                                                                                                                                        self.log('DEBUG',
                                                                                                                                                                                                            message,
                                                                                                                                                                                                            extra_data = kwargs,
                                                                                                                                                                                                            include_locals = True)

# Create global logger instance
                                                                                                                                                                                                        logger = MasterLogger(,)

                                                                                                                                                                                                        def log_exceptions(func):
                                                                                                                                                                                                            """Decorator to automatically log exceptions from any function."""
                                                                                                                                                                                                            def wrapper(*args,
                                                                                                                                                                                                                **kwargs):
                                                                                                                                                                                                                """TODO: Add docstring."""
                                                                                                                                                                                                                try:
                                                                                                                                                                                                                    return func(*args,
                                                                                                                                                                                                                        **kwargs)
                                                                                                                                                                                                                except Exception as e:
                                                                                                                                                                                                                    logger.error(
                                                                                                                                                                                                                    f'Exception in {func.__name__}',
                                                                                                                                                                                                                        
                                                                                                                                                                                                                    exception = e,
                                                                                                                                                                                                                        
                                                                                                                                                                                                                    function_name = func.__name__,
                                                                                                                                                                                                                        
                                                                                                                                                                                                                    function_doc = func.__doc__,
                                                                                                                                                                                                                        
                                                                                                                                                                                                                    args = repr(args)[: 500],
                                                                                                                                                                                                                        
                                                                                                                                                                                                                    kwargs = repr(kwargs)[: 500]
                                                                                                                                                                                                                    )
                                                                                                                                                                                                                    raise  # Re - raise the exception
                                                                                                                                                                                                                    wrapper.__name__ = func.__name__
                                                                                                                                                                                                                    wrapper.__doc__ = func.__doc__
                                                                                                                                                                                                                    return wrapper

                                                                                                                                                                                                                    def setup_global_exception_handler():
                                                                                                                                                                                                                        """Set up a global handler for uncaught exceptions."""
                                                                                                                                                                                                                        def handle_exception(exc_type,
                                                                                                                                                                                                                            exc_value,
                                                                                                                                                                                                                            exc_traceback):
                                                                                                                                                                                                                            """TODO: Add docstring."""
        # Don't log KeyboardInterrupt
                                                                                                                                                                                                                            if issubclass(exc_type,
                                                                                                                                                                                                                                KeyboardInterrupt):
                                                                                                                                                                                                                                sys.__excepthook__(exc_type,
                                                                                                                                                                                                                                    exc_value,
                                                                                                                                                                                                                                    exc_traceback)
                                                                                                                                                                                                                                return

                                                                                                                                                                                                                                logger.critical(
                                                                                                                                                                                                                                'UNCAUGHT EXCEPTION - Program may terminate',
                                                                                                                                                                                                                                    
                                                                                                                                                                                                                                exception = exc_value,
                                                                                                                                                                                                                                    
                                                                                                                                                                                                                                exc_type = str(exc_type),
                                                                                                                                                                                                                                    
                                                                                                                                                                                                                                traceback_obj = traceback.format_tb(exc_traceback,)
                                                                                                                                                                                                                                )

        # Call the default handler
                                                                                                                                                                                                                                sys.__excepthook__(exc_type,
                                                                                                                                                                                                                                    exc_value,
                                                                                                                                                                                                                                    exc_traceback)

                                                                                                                                                                                                                                sys.excepthook = handle_exception