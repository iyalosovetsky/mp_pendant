#Define realtime command special characters. These characters are 'picked-off' directly from the
#serial read data stream and are not passed to the grbl line execution parser. Select characters
#that do not and must not exist in the streamed g-code program. ASCII control characters may be
#used, if they are available per user setup. Also, extended ASCII codes (>127), which are never in
#g-code programs, maybe selected for interface programs.
#NOTE: If changed, manually update help message in report.c.
CMD_EXIT = 0x03 # ctrl-C (ETX)
CMD_REBOOT = 0x14 # ctrl-T (DC4) - only acted upon if preceded by 0x1B (ESC)
CMD_RESET = 0x18 # ctrl-X (CAN)
CMD_STOP = 0x19 # ctrl-Y (EM)
CMD_STATUS_REPORT_LEGACY = '?'
CMD_CYCLE_START_LEGACY = '~'
CMD_FEED_HOLD_LEGACY = '!'
CMD_PROGRAM_DEMARCATION = '%'

#NOTE: All override realtime commands must be in the extended ASCII character set, starting
#at character value 128 (0x80) and up to 255 (0xFF). If the normal set of realtime commands,
#such as status reports, feed hold, reset, and cycle start, are moved to the extended set
#space, protocol.c's protocol_process_realtime() will need to be modified to accommodate the change.
CMD_STATUS_REPORT = 0x80 # TODO: use 0x05 ctrl-E ENQ instead?
CMD_CYCLE_START = 0x81 # TODO: use 0x06 ctrl-F ACK instead? or SYN/DC2/DC3?
CMD_FEED_HOLD = 0x82 # TODO: use 0x15 ctrl-U NAK instead?
CMD_GCODE_REPORT = 0x83 
CMD_SAFETY_DOOR = 0x84
CMD_JOG_CANCEL  = 0x85
CMD_DEBUG_REPORT = 0x86 # Only when DEBUG enabled, sends debug report in '{}' braces.
CMD_STATUS_REPORT_ALL = 0x87
CMD_OPTIONAL_STOP_TOGGLE = 0x88
CMD_SINGLE_BLOCK_TOGGLE = 0x89
CMD_OVERRIDE_FAN0_TOGGLE = 0x8A #Toggle Fan 0 on/off, not implemented by the core.
CMD_MPG_MODE_TOGGLE = 0x8B       #Toggle MPG mode on/off
CMD_AUTO_REPORTING_TOGGLE = 0x8C #Toggle auto real time reporting if configured.
CMD_OVERRIDE_FEED_RESET = 0x90   #Restores feed override value to 100%.
CMD_OVERRIDE_FEED_COARSE_PLUS = 0x91 
CMD_OVERRIDE_FEED_COARSE_MINUS = 0x92
CMD_OVERRIDE_FEED_FINE_PLUS = 0x93 
CMD_OVERRIDE_FEED_FINE_MINUS = 0x94 
CMD_OVERRIDE_RAPID_RESET = 0x95  #Restores rapid override value to 100%.
CMD_OVERRIDE_RAPID_MEDIUM = 0x96 
CMD_OVERRIDE_RAPID_LOW = 0x97 
CMD_OVERRIDE_RAPID_EXTRA_LOW = 0x98 # *NOT SUPPORTED*
CMD_OVERRIDE_SPINDLE_RESET = 0x99 # Restores spindle override value to 100%.
CMD_OVERRIDE_SPINDLE_COARSE_PLUS = 0x9A
CMD_OVERRIDE_SPINDLE_COARSE_MINUS = 0x9B
CMD_OVERRIDE_SPINDLE_FINE_PLUS = 0x9C
CMD_OVERRIDE_SPINDLE_FINE_MINUS = 0x9D
CMD_OVERRIDE_SPINDLE_STOP = 0x9E
CMD_OVERRIDE_COOLANT_FLOOD_TOGGLE = 0xA0
CMD_OVERRIDE_COOLANT_MIST_TOGGLE = 0xA1
CMD_PID_REPORT = 0xA2
CMD_TOOL_ACK = 0xA3
CMD_PROBE_CONNECTED_TOGGLE = 0xA4

#   Alarm executor codes. Zero is reserved.   *************************
Alarm_HardLimit = 1
Alarm_SoftLimit = 2
Alarm_AbortCycle = 3
Alarm_ProbeFailInitial = 4
Alarm_ProbeFailContact = 5
Alarm_HomingFailReset = 6
Alarm_HomingFailDoor = 7
Alarm_FailPulloff = 8
Alarm_HomingFailApproach = 9
Alarm_EStop = 10
Alarm_HomingRequired = 11
Alarm_LimitsEngaged = 12
Alarm_ProbeProtect = 13
Alarm_Spindle = 14
Alarm_HomingFailAutoSquaringApproach = 15
Alarm_SelftestFailed = 16
Alarm_MotorFault = 17
Alarm_HomingFail = 18


# *************************************************************************
Status_OK = 0
Status_ExpectedCommandLetter = 1
Status_BadNumberFormat = 2
Status_InvalidStatement = 3
Status_NegativeValue = 4
Status_HomingDisabled = 5
Status_SettingStepPulseMin = 6
Status_SettingReadFail = 7
Status_IdleError = 8
Status_SystemGClock = 9
Status_SoftLimitError = 10
Status_Overflow = 11
Status_MaxStepRateExceeded = 12
Status_CheckDoor = 13
Status_LineLengthExceeded = 14
Status_TravelExceeded = 15
Status_InvalidJogCommand = 16
Status_SettingDisabledLaser = 17
Status_Reset = 18
Status_NonPositiveValue = 19

Status_GcodeUnsupportedCommand = 20
Status_GcodeModalGroupViolation = 21
Status_GcodeUndefinedFeedRate = 22
Status_GcodeCommandValueNotInteger = 23
Status_GcodeAxisCommandConflict = 24
Status_GcodeWordRepeated = 25
Status_GcodeNoAxisWords = 26
Status_GcodeInvalidLineNumber = 27
Status_GcodeValueWordMissing = 28
Status_GcodeUnsupportedCoordSys = 29
Status_GcodeG53InvalidMotionMode = 30
Status_GcodeAxisWordsExist = 31
Status_GcodeNoAxisWordsInPlane = 32
Status_GcodeInvalidTarget = 33
Status_GcodeArcRadiusError = 34
Status_GcodeNoOffsetsInPlane = 35
Status_GcodeUnusedWords = 36
Status_GcodeG43DynamicAxisError = 37
Status_GcodeIllegalToolTableEntry = 38
Status_GcodeValueOutOfRange = 39
Status_GcodeToolChangePending = 40
Status_GcodeSpindleNotRunning = 41
Status_GcodeIllegalPlane = 42
Status_GcodeMaxFeedRateExceeded = 43
Status_GcodeRPMOutOfRange = 44
Status_LimitsEngaged = 45
Status_HomingRequired = 46
Status_GCodeToolError = 47
Status_ValueWordConflict = 48
Status_SelfTestFailed = 49
Status_EStop = 50
Status_MotorFault = 51
Status_SettingValueOutOfRange = 52
Status_SettingDisabled = 53
Status_GcodeInvalidRetractPosition = 54
Status_IllegalHomingConfiguration = 55
Status_GCodeCoordSystemLocked = 56

#Some error codes as defined in bdring's ESP32 port
Status_SDMountError = 60
Status_SDReadError = 61
Status_SDFailedOpenDir = 62
Status_SDDirNotFound = 63
Status_SDFileEmpty = 64

Status_BTInitError = 70


Status_ExpressionUknownOp = 71
Status_ExpressionDivideByZero = 72
Status_ExpressionArgumentOutOfRange = 73
Status_ExpressionInvalidArgument = 74
Status_ExpressionSyntaxError = 75
Status_ExpressionInvalidResult = 76

Status_AuthenticationRequired = 77
Status_AccessDenied = 78
Status_NotAllowedCriticalEvent = 79

Status_FlowControlNotExecutingMacro = 80
Status_FlowControlSyntaxError = 81
Status_FlowControlStackOverflow = 82
Status_FlowControlOutOfMemory = 83



