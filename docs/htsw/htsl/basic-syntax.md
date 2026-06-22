# Basic Syntax

This is a collection of basic syntax elements with examples. You can find
 more examples in the [examples directory on GitHub](https://github.com/LGHousing/htsw/tree/main/examples).

## Comments

HTSL supports single-line (or **end-of-line**) and multi-line (**block**)
 comments.

```htsl
// This is an end-of-line comment

/* This is a block comment
   on multiple lines. */
```

## Actions

Every statement in HTSL represents an action.

Actions begin with a keyword and take a series of positional arguments:

```htsl
chat "Hello, World!"
tp Custom_Coordinates "0 0 0"
```

A newline terminates an action; All positional arguments must be on the same
 line.

You can find a detailed list of the syntax for all actions [here](actions.md).

## Conditions

You can find a detailed list of the syntax for all conditions
 [here](conditions.md).