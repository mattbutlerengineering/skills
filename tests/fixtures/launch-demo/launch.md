---
launch: fixture
date: 2026-10-08
sources: [tests/fixtures/launch-demo/index.html]
video: none — rendered by Verify into a throwaway publish directory
---

# Launch: the fixture page

## What it is

A single page with a counter and a greeter, kept in the plugin's own
tests so the browser recorder has something to drive. It loads from a
local server and asks nothing of the network.

## What it does

Pressing the counting button raises the number on the page by one.
Typing a name and pressing the greeting button writes a hello to that
name beneath it.

## How it helps

A recorder that can count and greet here can drive a real product page
the same way. The page never changes, so every recording of it is
comparable to the last.
