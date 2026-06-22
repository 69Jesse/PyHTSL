# Tooling

HTSW comes with an official CLI for checking and running HTSW imports.

## Installation

Currently, you must install the HTSW CLI by cloning the HTSW repository,
 building the CLI, and running `npm link`.

This may be streamlined later.

## Commands

### `htsw check`

Parses and validates the `import.json` file in the CWD, or an `import.json`
 pointed to by the optional positional argument.

### `htsw run`

Runs the function `htsw:main` of the `import.json` file in the CWD, or an
 `import.json` pointed to by the optional positional argument.

The output of the
 [Send a Chat Message](./htsl/actions.md#send-a-chat-message)
 action is redirected to the standard output.

> Note that repeating functions are ignored in `htsw run`.