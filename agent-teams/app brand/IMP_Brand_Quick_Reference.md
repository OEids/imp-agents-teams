# IMP Software Brand Quick Reference

For Excel tools, ICFP processors, and internal documents.

---

## Brand Colours

### Primary Colours (use these most often)
| Colour | Hex | RGB | Use for |
|--------|-----|-----|---------|
| Deep Purple | `#261342` | 38, 19, 66 | Headers, footers, primary backgrounds |
| Purple | `#6A0F8E` | 106, 15, 142 | Accents, secondary headers, "Behind" text |
| Light Purple | `#A093DB` | 160, 147, 219 | Product names, highlights, light accents |
| White | `#FFFFFF` | 255, 255, 255 | Text on dark backgrounds, page backgrounds |

### Accent Colours
| Colour | Hex | RGB | Use for |
|--------|-----|-----|---------|
| Violet | `#6C63FF` | 108, 99, 255 | Excelion graphic element |
| Cyan | `#67D1FF` | 103, 209, 255 | Excelion graphic element |
| Dark Grey | `#B2B2B2` | 178, 178, 178 | Support service names |
| Light Grey | `#E5E5E5` | 229, 229, 229 | Borders, subtle backgrounds |

---

## Excel Colour Application

### For Excel RGB values
```
Deep Purple:  RGB(38, 19, 66)
Purple:       RGB(106, 15, 142)
Light Purple: RGB(160, 147, 219)
Cyan:         RGB(103, 209, 255)
Violet:       RGB(108, 99, 255)
```

### Typical Excel usage
- **Title bars / Headers**: Deep Purple background, White text
- **Column headers**: Light Purple background, Deep Purple text
- **Highlight cells**: Cyan or Light Purple with subtle fill
- **Borders**: Light Grey (#E5E5E5) or Deep Purple
- **Error/warning**: Use Purple (#6A0F8E) not red

---

## Typography

### Primary fonts (if available)
- **Headings**: Kamerik 105 Bold
- **Body**: League Spartan Light/Medium

### Fallback fonts (for Excel/internal docs)
- **Corbel** - Microsoft default, approved for business use
- Use **Corbel Bold** for headings
- Use **Corbel Regular** for body text

### Font sizes (typical)
| Element | Size |
|---------|------|
| Main title | 18-24pt |
| Section header | 14-16pt |
| Body text | 10-12pt |
| Small text/captions | 8-10pt |

---

## Logo Usage

### Files available
- `imp_logo_final.png` - Cropped logo (Excelion + Wordmark) for headers
- `imp_logo.png` - Full letterhead background image

### Logo rules
- Only use on white (#FFFFFF) or Deep Purple (#261342) backgrounds
- Maintain clear space around logo (50% of logo height on all sides)
- Don't recreate or modify the logo
- The Excelion (grid symbol) can be used alone for favicons/app icons

### Product logo naming
- Format: "IMP [Product]" with product name in Light Purple (#A093DB)
- Examples: IMP Planner, IMP Purchasing

### Support service naming
- Format: "IMP [Service]" with service name in Dark Grey (#B2B2B2)
- Examples: IMP Voice, IMP Help

---

## Contact Details (for footers)

```
C/O Bishop Fleming,
Brook House, Manor Drive,
Clyst St. Mary, Exeter,
United Kingdom, EX5 1GD

01392 573 620
hello@impsoftware.co.uk
impsoftware.co.uk
```

---

## Voice & Tone Reminders

### Do
- Clear, simple language
- Short sentences
- Write as you'd talk (contractions OK)
- Use "we" and "you"
- Focus on what the customer needs

### Don't
- Technical jargon (unless audience knows it)
- Exclamation marks
- Verbose or wanky language
- Talk about ourselves instead of customer
- Sound pushy or arrogant

---

## Key Messaging

**Purpose**: "Support Smarter MAT Finance"

**Tagline format**: "Behind [noun]" 
- Behind Ambitious MAT Finance Teams
- Behind Clarity
- Behind Opportunity

---

## Quick VBA Colour Reference

```vba
' IMP Brand Colours for VBA
Const IMP_DEEP_PURPLE As Long = 4331302    ' RGB(38, 19, 66)
Const IMP_PURPLE As Long = 9310058         ' RGB(106, 15, 142)
Const IMP_LIGHT_PURPLE As Long = 14389152  ' RGB(160, 147, 219)
Const IMP_CYAN As Long = 16765287          ' RGB(103, 209, 255)
Const IMP_WHITE As Long = 16777215         ' RGB(255, 255, 255)
Const IMP_LIGHT_GREY As Long = 15066597    ' RGB(229, 229, 229)

' Usage example:
' Range("A1").Interior.Color = IMP_DEEP_PURPLE
' Range("A1").Font.Color = IMP_WHITE
```

---

*Reference: IMP Software Brand Guidelines (Aug 2022)*
