@echo off
REM fastReader Windows wrapper. Place this file inside the fastReader\ folder.
REM It sets PYTHONPATH to the parent of its own directory (so
REM `python -m fastReader.<subcmd>` can resolve) and dispatches the first
REM positional argument as the subcommand name.
REM
REM Optional `json` subcommand: if the sibling quick-json-reader skill is
REM installed at ..\quick-json-reader\quick-json-reader.exe (or wherever
REM FAST_READER_JSON_BIN points), `fastReader json <args>` pass-through
REM launches that binary.

SETLOCAL ENABLEDELAYEDEXPANSION

SET "FAST_READER_SCRIPT_DIR=%~dp0"
REM %~dp0 ends with a trailing backslash. Strip it, then take the parent.
SET "FAST_READER_SCRIPT_DIR=%FAST_READER_SCRIPT_DIR:~0,-1%"
FOR %%I IN ("%FAST_READER_SCRIPT_DIR%") DO SET "FAST_READER_SKILL_PARENT_DIR=%%~dpI"
SET "FAST_READER_SKILL_PARENT_DIR=%FAST_READER_SKILL_PARENT_DIR:~0,-1%"

SET "FAST_READER_DEFAULT_JSON_BIN_PATH=%FAST_READER_SKILL_PARENT_DIR%\quick-json-reader\quick-json-reader.exe"
IF NOT DEFINED FAST_READER_JSON_BIN SET "FAST_READER_JSON_BIN=%FAST_READER_DEFAULT_JSON_BIN_PATH%"

SET "FAST_READER_JSON_MODULE_AVAILABLE=0"
IF EXIST "%FAST_READER_JSON_BIN%" SET "FAST_READER_JSON_MODULE_AVAILABLE=1"

IF "%~1"=="" (
    CALL :PRINT_HELP
    EXIT /B 0
)

SET "FAST_READER_SUBCOMMAND_NAME=%~1"
SHIFT

IF /I "%FAST_READER_SUBCOMMAND_NAME%"=="load"   GOTO SUBCOMMAND_PY
IF /I "%FAST_READER_SUBCOMMAND_NAME%"=="toc"    GOTO SUBCOMMAND_PY
IF /I "%FAST_READER_SUBCOMMAND_NAME%"=="get"    GOTO SUBCOMMAND_PY
IF /I "%FAST_READER_SUBCOMMAND_NAME%"=="search" GOTO SUBCOMMAND_PY
IF /I "%FAST_READER_SUBCOMMAND_NAME%"=="json"   GOTO SUBCOMMAND_JSON
IF /I "%FAST_READER_SUBCOMMAND_NAME%"=="-h"     GOTO SHOW_HELP
IF /I "%FAST_READER_SUBCOMMAND_NAME%"=="--help" GOTO SHOW_HELP

ECHO fastReader: unknown subcommand '%FAST_READER_SUBCOMMAND_NAME%' 1>&2
IF "%FAST_READER_JSON_MODULE_AVAILABLE%"=="1" (
    ECHO valid: load, toc, get, search, json 1>&2
) ELSE (
    ECHO valid: load, toc, get, search  ^(install quick-json-reader skill to enable 'json'^) 1>&2
)
EXIT /B 2

:SHOW_HELP
CALL :PRINT_HELP
EXIT /B 0

:PRINT_HELP
ECHO usage: fastReader ^<subcommand^> [args...]
ECHO subcommands: load ^| toc ^| get ^| search
ECHO examples:
ECHO   fastReader load big_doc.md
ECHO   fastReader toc ^<hash^> --sections --show-line-range-count
ECHO   fastReader get ^<hash^> --section 3
ECHO   fastReader search error --manifests ^<hash^>
ECHO Add --help / --help-examples / --help-use-cases to any subcommand
ECHO for argparse flags, copy-paste recipes, or trigger-^>command mapping.
ECHO.
ECHO Optional module:
IF "%FAST_READER_JSON_MODULE_AVAILABLE%"=="1" (
    ECHO   json  ^(detected: %FAST_READER_JSON_BIN%^)
    ECHO         Pass-through to the quick-json-reader binary for JSON-specific
    ECHO         extraction/filtering. Example: fastReader json file.json --search-vals error
) ELSE (
    ECHO   json  ^(NOT INSTALLED^)
    ECHO         fastReader already efficiently parses and displays bracketed and
    ECHO         tagged text. For much more versatile JSON-specific integration -
    ECHO         schema inference, value search, field exclusion - install the
    ECHO         quick-json-reader skill alongside this one. When the binary is
    ECHO         detected at ^<skills-parent^>\quick-json-reader\quick-json-reader.exe
    ECHO         ^(or the FAST_READER_JSON_BIN env var^), the json module becomes
    ECHO         available automatically. No reinstall of fastReader required.
)
GOTO :EOF

:SUBCOMMAND_PY
REM Collect remaining args. cmd.exe has no "$@" equivalent, so we rebuild
REM with a shift-loop. Preserves quoted args reasonably well.
SET "FAST_READER_FORWARDED_ARGS="
:ARG_LOOP_PY
IF "%~1"=="" GOTO RUN_PYTHON
SET "FAST_READER_FORWARDED_ARGS=%FAST_READER_FORWARDED_ARGS% %1"
SHIFT
GOTO ARG_LOOP_PY

:RUN_PYTHON
SET "PYTHONPATH=%FAST_READER_SKILL_PARENT_DIR%"
python -m fastReader.%FAST_READER_SUBCOMMAND_NAME%%FAST_READER_FORWARDED_ARGS%
EXIT /B %ERRORLEVEL%

:SUBCOMMAND_JSON
IF "%FAST_READER_JSON_MODULE_AVAILABLE%"=="0" (
    ECHO fastReader: the 'json' module requires the quick-json-reader skill. 1>&2
    ECHO Expected binary at: %FAST_READER_JSON_BIN% 1>&2
    ECHO Install the quick-json-reader skill alongside fastReader, or set 1>&2
    ECHO FAST_READER_JSON_BIN to an absolute path to the binary. 1>&2
    EXIT /B 3
)
SET "FAST_READER_JSON_FORWARDED_ARGS="
:ARG_LOOP_JSON
IF "%~1"=="" GOTO RUN_JSON
SET "FAST_READER_JSON_FORWARDED_ARGS=%FAST_READER_JSON_FORWARDED_ARGS% %1"
SHIFT
GOTO ARG_LOOP_JSON

:RUN_JSON
"%FAST_READER_JSON_BIN%"%FAST_READER_JSON_FORWARDED_ARGS%
EXIT /B %ERRORLEVEL%
