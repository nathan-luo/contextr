# Course Correction: Story 3.1 Replacement

## Date: 2025-07-26

## Decision: Replace Profile Templates with Watch/Context Simplification

### Original Story 3.1: Profile Templates
The original story focused on creating predefined profile templates for common project types (Python, JavaScript, etc.). While useful, this didn't address the core usability issues identified by the user.

### New Story 3.1: Watch/Context Simplification and Gitignore Integration
Based on user feedback, we've pivoted to address more fundamental UX improvements:

1. **Simplify the watch/context abstraction** - The current separation between "watched patterns" and "context files" is confusing. The new approach makes context automatically sync with watched patterns, removing the need for separate file management.

2. **Integrate gitignore sync into profile creation** - Add a `--gis` flag to the new `ctxr profile new` command, making it easy to exclude commonly ignored files when setting up a profile.

3. **Shorten command names** - Rename `gitignore-sync` to `gis` for faster typing and better ergonomics.

### Why This Change?

The user identified that the current tool has unnecessary complexity:
- Having to manage both "watched patterns" and "context files" separately is confusing
- The relationship between these concepts isn't clear
- Common operations like syncing gitignore require too much typing

The new story addresses these pain points by:
- Making the tool work the way users expect (watch = context)
- Reducing the number of concepts users need to understand
- Making common operations more convenient

### Implementation Impact

This change will:
- Simplify the mental model for users
- Reduce the number of commands needed
- Make the tool more intuitive for new users
- Maintain backward compatibility with existing saved states and profiles

### Next Steps

1. Implement Story 3.1: Watch/Context Simplification
2. Update documentation to reflect the simplified model
3. Consider future stories that build on this simplified foundation

## YOLO Mode Decision

The user selected Option 2 (YOLO Mode) for this course correction, authorizing immediate implementation without further review.