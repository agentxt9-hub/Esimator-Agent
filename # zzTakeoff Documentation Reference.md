# zzTakeoff Documentation Reference

> Complete guides and reference materials to help you get the most out of zzTakeoff.
>
> Source: https://www.zztakeoff.com/app/community/documentation

---

# Getting Started - How to

---

## Creating a New Project in zzTakeoff

### Initial Setup

#### 1. Launch Project Creation

- Click the dropdown menu in the top-left corner - (1)
- Select "New Project" from the options - (2)

#### 2. Configure Project Settings

In the project setup dialog box:

- Choose your workspace location - (1)
- Enter a unique project name - (2)
- Select your measurement system (Imperial or Metric) - (3)
- Click "Create Project" to proceed - (4)

### Adding Project Files

#### 1. Upload Documents

In the file upload dialog:

- Click to browse and select files from your computer - (1)
- Drag and drop files directly onto the upload area, or - (2)
- Click "Next" to continue - (3)

#### 2. File Selection and Confirmation

- Review the list of uploaded Pages/Sheets - (1)
- Select or deselect specific Pages to include - (2)
- Click "Upload" to begin file processing - (3)

#### 3. Completion

- Monitor the progress bar as files are processed
- Wait for confirmation that files have been successfully uploaded
- Your project will automatically open once setup is complete

### Tips for Success

- Ensure all files are in supported formats before uploading (i.e. PDF, PNG, JPG, TIFF)
- Choose a descriptive project name that helps identify the project
- Verify your measurement system selection before creating the project, as this setting cannot be changed later

---

## Scaling Pages in zzTakeoff

### Overview

Two methods available for scaling pages:

- AI-powered automatic scaling
- Manual scaling using known dimensions

### Method 1: AI-Powered Automatic Scaling

1. Find the Scale on Selected page in the project
2. Highlight the Scale by drawing a Window around the Scale
3. From the Context Menu Click "Scale"
4. Wait for AI analysis of the drawing
5. AI detects standard dimensions
6. Sets the appropriate scale
7. Check scale is set in the Scale Dropdown from the top ribbon toolbar, or check for Cross Hair on the Left Hand Side
8. Verify scale accuracy using a known dimension (both Vertical & Horizontal is recommended)

### Method 2: Manual Scaling

1. Select your target page
2. Click the "Scale" tool in the top ribbon toolbar
3. Find a known dimension on drawing
4. Scale the drawing:
   - Enter known dimension and click start
   - Click start point of dimension
   - Click end point of dimension
   - For more precision repeat this process for both Horizontal & Vertical measurement

> **Note:** It is recommended to confirm scale for each page of the project using a known dimension in both directions.

### Important Notes

- Always verify scale accuracy after setting
- AI scaling works best with standard architectural/engineering scales
- Manual scaling provides more precise control

---

## Page Naming and Numbering using AI

### Overview

zzTakeoff's AI-powered page naming and numbering feature helps you efficiently manage and organize project pages with automated updating across your entire project.

**Key Benefits:**

- Streamlined page organization
- AI-powered naming suggestions
- Time-saving batch operations
- Reduced manual errors

### Naming Pages

1. On any page in your project, locate the page name on the page
2. Highlight the existing page name
3. The dynamic menu will automatically open
4. Choose "All" next to the AI-powered renaming function
5. The AI will automatically rename the pages
6. Confirm the changes are correct

### Numbering Pages

1. Select any page to commence the renumber
2. Locate the page number on the page
3. Highlight the current page number
4. The dynamic menu will automatically open
5. Choose "All" next to the AI-powered renumbering function
6. The AI will automatically renumber the pages
7. Confirm the changes are correct

---

## How to Export Data to Excel or CSV

### Method 1: Using the Reports Tab

1. Navigate to the Reports tab in the top navigation menu
2. Right-click anywhere on the data grid
3. In the context menu that appears, hover over "Export"
4. Select your desired export format:
   - Choose "CSV Export" for a comma-separated values file
   - Choose "Excel Export" for a Microsoft Excel file

### Method 2: Using the Takeoff Totals Export Icon

1. Go to the Takeoff tab
2. Locate the Takeoff Totals panel on the right side of the screen
3. Find the export icon in the top-right corner of the Takeoff Totals panel
4. Click the export icon
5. Choose your preferred export format:
   - CSV Export
   - Excel Export

### Common Uses

- Exporting quantity takeoffs for estimation
- Sharing project data with team members
- Creating backup copies of measurements
- Generating reports for clients or stakeholders
- Further analysis in spreadsheet software

---

## List of Current Hotkeys

| Key | Action |
|-----|--------|
| `C` | Completes takeoff (same as Escape) |
| `A` | Toggle Arc point - only if 1 point is selected |
| `N` | New section |
| `T` `B` `L` `R` | Align points in that direction (if you have 2 selected) |
| `Backspace` | Back out (Undo) last point clicked |
| `Escape` | Complete current takeoff |
| `Arrow keys` | Move the exact distance after initial click |
| `ALT` + Hold Left Mouse | Move a takeoff item(s) |
| Mouse Wheel Forward | Zoom In |
| Mouse Wheel Back | Zoom Out |
| Hold Left Mouse (AI SmartSelect) | Focus AI over printed scales, page names, create takeoff items, extract schedules, copy schedules to clipboard |
| `Middle Click` (scroll wheel press) | Open pages in new tabs. Tabs can be docked or viewed simultaneously. Each tab is a fully functional zzTakeoff instance. |
| `CTRL + S` or `CTRL + Enter` | Completes any Dialog instead of clicking Save Button |

---

## Arc Tool Documentation

### Overview

The Arc Tool allows you to create curved segments in both lines and areas within zzTakeoff. This tool is accessed using the keyboard shortcut "A" and can be utilized in multiple workflows.

### Creating an Arc Line

**Method 1 - Creating a New Arc:**

1. Start by clicking your first point to begin the line
2. Press the "A" key on your keyboard to activate the Arc Tool
3. Click a second point to define the path of the arc
4. Click a third point to complete the arc segment

**Method 2 - Adding an Arc to an Existing Line:**

1. Double click along an existing line to add a new node (point) between two existing nodes
2. Move the new middle point to your desired position along the curved path
3. With the middle node selected, press "A" to convert the segment into an arc

### Creating an Arc in an Area

The Arc Tool can also be used while creating areas:

1. Begin your area measurement with an initial click
2. Press "A" to activate the Arc Tool
3. Click to create the arc segment
4. Continue adding straight or curved segments as needed
5. Press "C" to complete the area measurement

### Key Points

- The Arc Tool works for both linear and area measurements
- Press "A" to toggle arc mode on/off during any measurement
- Arcs are three-point curves (start, path, end)
- Double-clicking existing lines allows you to add arc segments retroactively

---

## Unlocking Powerful Calculations: Introducing Formulas for Takeoffs and Templates

### Overview

With the introduction of "Items that can be used in Takeoffs and Templates," you can leverage the measurements taken directly within your Takeoffs to perform dynamic calculations, thanks to the integration of robust mathematical capabilities. You can create intelligent items that automatically compute values based on real-world dimensions like "Area," "Volume," "Linear," and more.

The Formula field includes a user-friendly "Insert" dropdown that provides a direct link to all available measurements and variables from your Takeoffs, allowing you to easily build complex calculations.

Behind the scenes, these formulas are powered by math.js, providing a flexible and comprehensive way to define your calculations. Whether you need to determine material quantities, labor costs, or any other value dependent on your takeoff measurements, Formulas will revolutionize your workflow.

### Basic Arithmetic Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `+` | Addition | `5 + 3 = 8` |
| `-` | Subtraction | `10 - 4 = 6` |
| `*` | Multiplication | `6 * 7 = 42` |
| `/` | Division | `15 / 3 = 5` |
| `^` or `**` | Power/Exponentiation | `2^3 = 8` or `2**3 = 8` |
| `%` | Modulo (remainder) | `10 % 3 = 1` |
| `!` | Factorial | `5! = 120` |

### Comparison Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `==` | Equal to | `5 == 5` returns true |
| `!=` | Not equal to | `5 != 3` returns true |
| `<` | Less than | `3 < 5` returns true |
| `>` | Greater than | `5 > 3` returns true |
| `<=` | Less than or equal | `3 <= 5` returns true |
| `>=` | Greater than or equal | `5 >= 5` returns true |

### Logical Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `and` | Logical AND | `true and false = false` |
| `or` | Logical OR | `true or false = true` |
| `not` | Logical NOT | `not true = false` |
| `xor` | Exclusive OR | `true xor false = true` |

### Essential Mathematical Functions

#### Rounding & Number Functions

| Function | Description | Example | Use Case |
|----------|-------------|---------|----------|
| `abs(x)` | Absolute value | `abs(-5) = 5` | Distance calculations |
| `ceil(x)` | Round up to nearest integer | `ceil(4.3) = 5` | Material quantities (always round up) |
| `floor(x)` | Round down to nearest integer | `floor(4.7) = 4` | Sheet counts, full units only |
| `round(x)` | Round to nearest integer | `round(4.6) = 5` | General rounding |
| `round(x, n)` | Round to n decimal places | `round(4.567, 2) = 4.57` | Currency, measurements |
| `sign(x)` | Sign of number (-1, 0, or 1) | `sign(-5) = -1` | Direction indicators |
| `min(a,b,...)` | Minimum value | `min(3, 7, 2) = 2` | Cost comparisons |
| `max(a,b,...)` | Maximum value | `max(3, 7, 2) = 7` | Load calculations |

#### Power & Root Functions

| Function | Description | Example | Use Case |
|----------|-------------|---------|----------|
| `sqrt(x)` | Square root | `sqrt(16) = 4` | Area to side length |
| `cbrt(x)` | Cube root | `cbrt(27) = 3` | Volume to side length |
| `pow(x, y)` | x raised to power y | `pow(2, 3) = 8` | Exponential calculations |
| `exp(x)` | e raised to power x | `exp(1) = 2.718...` | Exponential growth |
| `log(x)` | Natural logarithm | `log(2.718) = 1` | Decay calculations |
| `log10(x)` | Base-10 logarithm | `log10(100) = 2` | Scale conversions |

#### Trigonometric Functions

| Function | Description | Example | Use Case |
|----------|-------------|---------|----------|
| `sin(x)` | Sine (x in radians) | `sin(pi/2) = 1` | Angle calculations |
| `cos(x)` | Cosine (x in radians) | `cos(0) = 1` | Component forces |
| `tan(x)` | Tangent (x in radians) | `tan(pi/4) = 1` | Slope calculations |
| `asin(x)` | Inverse sine | `asin(1) = pi/2` | Finding angles |
| `acos(x)` | Inverse cosine | `acos(1) = 0` | Finding angles |
| `atan(x)` | Inverse tangent | `atan(1) = pi/4` | Finding angles |
| `atan2(y,x)` | Two-argument arctangent | `atan2(1,1) = pi/4` | Angle from coordinates |

#### Statistical Functions

| Function | Description | Example | Use Case |
|----------|-------------|---------|----------|
| `mean([...])` | Average of values | `mean([1,2,3,4]) = 2.5` | Average costs, dimensions |
| `median([...])` | Middle value | `median([1,2,3,4,5]) = 3` | Typical values |
| `sum([...])` | Sum of all values | `sum([1,2,3,4]) = 10` | Total quantities |
| `std([...])` | Standard deviation | `std([1,2,3,4,5]) = 1.58` | Variation analysis |
| `var([...])` | Variance | `var([1,2,3,4,5]) = 2.5` | Spread of data |

### Constants

| Constant | Value | Description | Use Case |
|----------|-------|-------------|----------|
| `pi` | 3.14159... | Pi (π) | Circle calculations |
| `e` | 2.71828... | Euler's number | Natural growth |
| `tau` | 6.28318... | 2π | Full circle (alternative to 2*pi) |
| `phi` | 1.61803... | Golden ratio | Proportional designs |

### Conditional Logic

| Function | Description | Example |
|----------|-------------|---------|
| `if(condition, valueIfTrue, valueIfFalse)` | Conditional value | `if(length > 10, 'long', 'short')` |

### Common Generic Construction/Estimating Formulas

#### Area Calculations

```
Rectangle: length * width
Circle: pi * radius^2
Triangle: 0.5 * base * height
```

#### Volume Calculations

```
Rectangular: length * width * height
Cylinder: pi * radius^2 * height
Sphere: (4/3) * pi * radius^3
```

#### Unit Conversions (Examples)

```
Feet to Inches: feet * 12
Square feet to square inches: sqft * 144
Cubic feet to cubic yards: cuft / 27
```

#### Waste Factor Applications

```
Material with 10% waste: quantity * 1.10
Material with waste factor: quantity * (1 + wasteFactor)
```

#### Rounding for Material Orders

```
Round up sheets: ceil(calculatedSheets)
Round to nearest 5: round(quantity / 5) * 5
Round to nearest 10: round(quantity / 10) * 10
```

### Usage Notes

- **Parentheses** control order of operations: `(2 + 3) * 4 = 20`
- **Arrays** use square brackets: `[1, 2, 3, 4]`
- **Angles** in trigonometric functions are in radians (multiply degrees by `pi/180`)
- **Variables** can be used: assign values and reference in formulas
- **Nested functions** are supported: `round(sqrt(area), 2)`

### Example Formulas for Estimating

```
// Concrete volume with 5% waste
concreteYards = ceil([Volume] / 27 * 1.05)

// Rebar weight calculation
rebarWeight = [Linear] * 3.4  // #6 rebar = 3.4 lbs/ft

// Paint coverage (assuming 350 sqft per gallon)
paintGallons = ceil([Area] / 350)

// Roofing squares (100 sqft = 1 square)
roofingSquares = ceil([Area] / 100)
```

---

## Planswift Migration

### How to Migrate Jobs and Templates from Planswift to zzTakeoff

### Introduction

Welcome to the zzTakeoff migration guide! This documentation will walk you through the process of importing your existing Planswift jobs and templates into zzTakeoff, helping you transition seamlessly to our platform while preserving your valuable takeoff data.

> **Important Disclaimer:** zzTakeoff is an independent software platform and has no association, affiliations, or endorsements with Planswift or its parent company Construct Connect. This migration functionality is provided as a convenience to users who wish to transition their data. All trademarks and product names mentioned belong to their respective owners.

### About This Guide

This migration guide represents an evolving resource that will be regularly updated as zzTakeoff continues to enhance its import capabilities.

### What Gets Imported

**For Projects (Jobs):**

- Basic project information
- Takeoff items and measurements
- Page/drawing associations
- Standard item properties

**For Templates:**

- Takeoff items (basic structure)
- Takeoff Items categories and organization
- Standard Takeoff items properties

### Current Limitations

**Project Import Limitations:**

- Formulas are not imported — Any formula-based calculations or scripts will need to be recreated manually
- Complex custom properties may require manual recreation
- Advanced markup styles may need adjustment

**Template Import Limitations:**

- Only Takeoff Items are currently imported
- Formula Parts and Assemblies are not imported — these will need to be rebuilt manually
- Complex template hierarchies may need restructuring
- New import capabilities are added regularly

### Getting Support

If you encounter issues during the migration process or have questions about specific features, please reach out to the zzTakeoff community or support team.

### Import Planswift Job into a zzTakeoff Project

**Step 1:** Access the Import Function — Start from the main zzTakeoff interface and click the "Open Project" button to access project options.

**Step 2:** Navigate to Import Projects — From the left sidebar menu, select "Import Projects" (highlighted in yellow with a red arrow indicator).

**Step 3:** Select Import Source — Choose "Planswift" from the available import options.

**Step 4:** Select Your Planswift Folder — Browse to or drag-and-drop the folder containing your Planswift projects. Alternatively, click "Choose a Folder" button or use the "drag & drop a folder here" option.

**Step 5:** Locate PlanSwift Projects — The default PlanSwift project location is typically:

```
C:\Program Files (x86)\PlanSwift11\Data\Storages\Local\Jobs
```

(though your projects may be at a different path)

**Step 6:** Important Import Limitations — Note the warning message: This import will include Pages, Area, Linear, Segment, and Count items. However, some data may not fully import, including:

- Sloped Areas
- Assemblies
- Parts
- Some Notes and Annotations

The process allows you to transfer your PlanSwift takeoff work into zzTakeoff's platform while preserving the core measurement data.

---

# Templates & Formulas

---

## Formula Builder Help Guide

### Getting Started with Formulas

Math.js formulas in ZZ allow you to create conditional calculations based on your takeoff properties. This guide will walk you through the basics and provide practical examples.

> **Important Note:** When copying formulas from this guide into ZZ's calculation window, you'll need to retype them rather than copy-paste, as formatting may not carry over properly.

### Basic Formula Structure

All conditional formulas follow this pattern:

```
if([Property] condition value, result_if_true, result_if_false)
```

### Breaking Down a Basic Formula

Let's examine this example: `if([Point Count]>=4, 8, 1)`

1. `if` — Starts every conditional formula
2. `([Point Count]>=4,` — The condition to test (is Point Count greater than or equal to 4?)
3. `8,` — The result if the condition is TRUE
4. `1` — The result if the condition is FALSE

**Result:** If Point Count is 4 or higher, the formula returns 8. If Point Count is less than 4, it returns 1.

### Comparison Operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `>=` | Greater than or equal to | `[Height]>=6` |
| `<=` | Less than or equal to | `[Width]<=10` |
| `>` | Greater than | `[Length]>8` |
| `<` | Less than | `[Count]<5` |
| `==` | Exactly equal to | `[Wall Thickness]==8` |

### Practical Examples

#### Example 1: Delivery Fee Calculation

```
if([Volume:CY]/[Truck Load CY]>= 10, 0, 1)
```

**What it does:** Calculates delivery charges based on truck loads

- If 10 or more truck loads: No delivery fee (0)
- If less than 10 truck loads: Add delivery fee (1)

#### Example 2: Material Length Selection

```
if([Linear:FT]<8, 1, 0)
```

**What it does:** Determines if you need 8-foot boards

- If measured length is less than 8 feet: Use 1 eight-foot board
- If measured length is 8 feet or more: Use 0 eight-foot boards

#### Example 3: Post Height Adjustments

```
(if([Post Height]>=6, 1, 0) + [Number of Clamps per Post]) * [Point Count]
```

**What it does:** Adds extra clamps for tall posts

- If post is 6 feet or taller: Add 1 extra clamp per post
- If post is shorter than 6 feet: No extra clamps

### Advanced Formulas

#### Combining Multiple Conditions

```
if(and([Linear:FT]>8, [Linear:FT]<=10), 1, 0)
```

**What it does:** Checks if length falls within a specific range (greater than 8 AND less than or equal to 10)

#### Chaining Calculations

```
if([Point Count]>=4, 8, 1) * ([Volume:CY]/13)
```

**What it does:** First determines a base value, then multiplies by another calculation

#### Using Properties in Results

```
if([Point Count]<4, [Any Value], [Value of Anything]) + [Point Count]
```

**What it does:** Uses different property values as results rather than fixed numbers

### Yes/No Switches

You can create dropdown switches in Custom Properties that work like checkboxes:

- **Yes = 1** (true)
- **No = 0** (false)

#### Setting Up a Yes/No Switch

1. Create a **Value & Name** Custom Property
2. Set up two options:
   - Name: "Yes", Value: 1
   - Name: "No", Value: 0
3. Apply to your takeoff properties (e.g., Linear and Segmented Takeoffs)

#### Using Yes/No Switches in Formulas

```
[Point Count] * [Calculate Post Caps]
```

**What it does:**

- If "Calculate Post Caps" is set to Yes (1): Calculates post caps normally
- If "Calculate Post Caps" is set to No (0): Results in zero quantity

### Common Use Cases for Other Formulas

#### Wall Thickness Calculations

```
if([Wall Thickness]==8, 1, 2) * [Linear:FT]/[Length of Product]
```

**Use case:** Different material quantities based on wall thickness

#### Production Rate Adjustments

```
((if([Post Height]>=6, 1,[Percentage of Increase], 1) * [Point Count]))/[Production Rate]
```

**Use case:** Adjust labor hours based on working height

#### Material Requirements with Switches

```
if([Wall Thickness]==8, 2, 1) * [Linear:FT]/[Length of Product] * [Sill Seal Required?]
```

**Use case:** Calculate materials only when needed, with quantity varying by specification

### Tips for Success

- **Test your formulas** with different values to ensure they work as expected
- **Use descriptive property names** to make formulas easier to understand
- **Break complex formulas** into smaller parts when possible
- **Document your formulas** do this in a shared document so others can understand and maintain them
- **Remember that property values** from takeoff level carry down to item level automatically providing you have the Same Property on that level

### Getting Help

If you're having trouble with a formula:

1. Check your parentheses — every opening parenthesis needs a closing one
2. Verify property names are exactly as they appear in your takeoff
3. Test with simple values first, then add complexity
4. Make sure comparison operators are appropriate for your data type (currently the Formula Field is for Quantities on the Items so the result needs to be a number)

---

## True/False Statements and Check Boxes

### Overview

Check boxes in takeoff software serve as true/false indicators for formulas. Understanding how these work is essential for creating dynamic calculations.

**Key Concepts:**

- **Checked box** = True = 1
- **Unchecked box** = False = 0

### Basic Usage

You can use check boxes to control whether quantities are included in calculations by multiplying or adding the checkbox variable.

**Example Formula:**

```
[Point Count] * [Include in Bid?]
```

**Results:**

- When checkbox is **checked (true):** Formula calculates normally
- When checkbox is **unchecked (false):** Result becomes zero

### AND Statements (&&)

**Purpose:** Use AND statements when **all conditions** must be true for the formula to return a positive result. If any condition is false, the entire expression evaluates to false.

**Syntax:**

```
(condition1 && condition2 && condition3) * [value]
```

**Example:**

```
(if([Point Count]>=10,1,0) && if([Width]>=2,1,0)) * [Point Count]
```

**How it works:**

- **Both conditions true:** Returns the calculated value
- **Any condition false:** Returns zero

**Sample Results:**

- Point Count = 10, Width = 2: Both true → Returns 10
- Point Count = 11, Width = 1: Width condition false → Returns 0

### OR Statements (||)

**Purpose:** Use OR statements when **at least one condition** must be true for the formula to return a positive result. Only one condition needs to be satisfied.

**Syntax:**

```
(condition1 || condition2 || condition3) * [value]
```

**Example:**

```
(if([Point Count]>=12,1,0) || if([Width]>=5,1,0)) * 1
```

**How it works:**

- **Any condition true:** Returns the calculated value
- **All conditions false:** Returns zero

**Sample Results:**

- Point Count = 8, Width = 5: Width condition true → Returns 1
- Point Count = 15, Width = 3: Point Count condition true → Returns 1
- Point Count = 8, Width = 3: Both conditions false → Returns 0

### Best Practices

**Formula Construction:**

1. **Test your conditions** individually before combining them
2. **Use parentheses** to group logical operations clearly
3. **Multiply by zero** to exclude items from calculations
4. **Combine with other variables** for complex conditional logic

**Common Use Cases:**

- **Quality control:** Only include measurements that meet specifications
- **Bid inclusion:** Toggle items in or out of cost calculations
- **Material optimization:** Apply different Materials based on dimensions

**Troubleshooting:**

- **Unexpected zeros:** Check if all AND (&&) conditions are satisfied
- **Always getting results:** Verify OR (||) conditions aren't too permissive
- **Formula errors:** Ensure proper parentheses grouping
- **Logic issues:** Test each condition separately first

### Quick Reference

| Operator | Symbol | Purpose | Result when TRUE | Result when FALSE |
|----------|--------|---------|------------------|-------------------|
| Check Box | N/A | Simple true/false | 1 | 0 |
| AND | `&&` | All must be true | Calculation proceeds | Returns 0 |
| OR | `\|\|` | At least one true | Calculation proceeds | Returns 0 |

> **Remember:** These logical operators are powerful tools for creating intelligent, conditional formulas that adapt based on your project requirements and user inputs.

---

# Product Development

---

## Test Server Access

We have a Test Server where we deploy features before release. The purpose of this server is to allow users to test and provide feedback on features we are developing.

If you're interested in playing with the latest features and providing feedback for us, you can [Request Test Server Access](https://www.zztakeoff.com) from the zzTakeoff team.

Thanks for all your help to make zzTakeoff the best it can be.

---

*This reference document was compiled from the zzTakeoff Community Documentation.*
*Source: https://www.zztakeoff.com/app/community/documentation*