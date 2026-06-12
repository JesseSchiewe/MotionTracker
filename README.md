# MotionTracker

MotionTracker is a Windows-first escape room motion tracking system built around Kinect v2.

## Goals

- Detect wand-like spell gestures from tracked hand motion.
- Detect multi-person body poses such as an X stance.
- Trigger puzzle outputs such as local audio cues and future unlock integrations.

## Architecture

The project is split into two parts:

- `src/python`: Python application for motion processing, gesture detection, puzzle rules, and outputs.
- `src/bridge`: C# Kinect v2 bridge that talks to the installed Kinect SDK and streams body frames to the Python app.

The bridge is scaffolded in this repository, but the Python app is the first runnable milestone.

## Current status

This repository currently contains the foundational Python package layout and the first implementation scaffolding for live and replay body-frame processing.
