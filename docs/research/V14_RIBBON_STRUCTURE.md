# Struktur Ribbon Nitro PDF Pro 14.41.0.15

**Status:** DRAFT v1
**Sumber:** identifier kontrol `AVRibbon:*` yang diekstraksi read-only
dari 30 modul engine (bukti `E-401`).
**Ekstraksi:** `scripts/extract_native_strings.py` →
`scripts/build_ribbon_map.py`

> Rekonstruksi ini **menggantikan** pengamatan UI langsung yang tidak
> mungkin dilakukan pada instalasi ini. Nama kontrol berasal dari
> binary build **v14.41.0.15** yang terpasang, jadi berbeda dari
> dokumentasi versi lain.

**783 kontrol** · **14 tab** · **543 grup**

## Tipe kontrol

| Scope | Jumlah |
|---|---:|
| `Control` | 460 |
| `Panel` | 131 |
| `Category` | 58 |
| `Element` | 44 |
| `SubElement` | 24 |
| `Btn` | 17 |
| `Edit` | 16 |
| `Categories` | 14 |
| `Group` | 10 |
| `Separator` | 5 |
| `Label` | 4 |

## Tab `(kontekstual)`

### Grup `%s`

- *Modul:* np_objects.dll

  - Edit

### Grup `Activate`

- *Modul:* NitroPDF.exe

  - Btn

### Grup `AddImage`

- *Modul:* np_annotations.dll, np_objects.dll

  - Btn

### Grup `Alignment`

- *Modul:* np_annotations.dll, np_forms.dll

### Grup `AnnotProp`

- *Modul:* np_annotations.dll

  - Appearance
  - Color
  - DummyHorizSeparator0001
  - DummyHorizSeparator01
  - DummyHorizSeparator02
  - DummyHorizSeparator03
  - DummyHorizSeparator1
  - DummyHorizSeparator2
  - DummyHorizSeparator22
  - DummyHorizSeparator23
  - DummyHorizSeparator3
  - DummyHorizSeparator4
  - DummyHorizSeparator5
  - DummyVertSeparator3
  - End
  - FillColor
  - General
  - LeaderExtension
  - LeaderLength
  - LeaderOffset
  - Line › Author
  - Line › Subject
  - More
  - More › Properties
  - More › SetAsDefault
  - Opacity
  - Start
  - Style
  - Thickness

### Grup `Area`

- *Modul:* np_annotations.dll

  - Btn

### Grup `Arrow`

- *Modul:* np_annotations.dll

  - Btn

### Grup `AutoBuildBookmarks`

- *Modul:* np_bookmarks.dll

  - Btn

### Grup `AutoKeywordLinks`

- *Modul:* np_links.dll

  - Btn

### Grup `AutoPageLinks`

- *Modul:* np_links.dll

  - Btn

### Grup `Backstage`

- *Modul:* NitroPDF.exe

  - FileSend › Btn
  - Open › Btn
  - SaveAs › Btn
  - SaveAsFlatten › Btn

### Grup `BatesNumbering`

- *Modul:* np_smart_tips.dll, np_stamper.dll

  - Btn
  - CurrentDocument › Btn
  - MultipleFiles › Btn
  - RemoveBatesNumbering › Btn

### Grup `Bookmark`

- *Modul:* NitroPDF.exe, np_bookmarks.dll, np_smart_tips.dll

  - Btn

### Grup `BuyNow`

- *Modul:* NitroPDF.exe

  - Label
  - Label2

### Grup `Calibration`

- *Modul:* np_annotations.dll

  - Btn

### Grup `CallOut`

- *Modul:* np_annotations.dll, np_smart_tips.dll

  - Btn

### Grup `Cloud`

- *Modul:* np_annotations.dll

  - Btn

### Grup `Console`

- *Modul:* np_smart_tips.dll

  - Btn

### Grup `ContextAnnotProps`

- *Modul:* np_annotations.dll

### Grup `CreateTags`

- *Modul:* np_accessibility.dll

  - Artifacts
  - Artifacts › RemoveBtn
  - Create
  - Create › Btn
  - Finish › Btn
  - TagProperties
  - TagProperties › TagType
  - Tagging
  - View
  - View › ShowArtifact
  - View › ShowContent

### Grup `CreateWeblinks`

- *Modul:* np_links.dll

  - Btn

### Grup `Crop`

- *Modul:* np_page_edit.dll

  - Advanced › Btn
  - Apply_crop › Btn
  - Category
  - HeightEdit › Btn
  - Landscape › Btn › %d
  - Measure_with_original › Btn
  - Portrait › Btn › %d
  - WidthEdit › Btn

### Grup `CropToolsCRC`

- *Modul:* np_page_edit.dll

  - CropEdit
  - CropResizing
  - Croppping
  - Separator1
  - Separator2

### Grup `CrossoutText`

- *Modul:* np_annotations.dll, np_smart_tips.dll

  - Btn

### Grup `DeleteAllBookmarks`

- *Modul:* np_bookmarks.dll

  - Btn

### Grup `Distance`

- *Modul:* np_annotations.dll

  - Btn

### Grup `DocumentActions`

- *Modul:* np_smart_tips.dll

  - Btn

### Grup `DocumentLevel`

- *Modul:* np_smart_tips.dll

  - Btn

### Grup `EditLinks`

- *Modul:* np_links.dll

  - Btn

### Grup `Empty`

- *Modul:* np_annotations.dll, np_forms.dll, np_links.dll, np_objects.dll

### Grup `ExportComments`

- *Modul:* np_annotations.dll

  - Btn

### Grup `FavoriteTools`

- *Modul:* NitroPDF.exe, np_smart_tips.dll

### Grup `File`

- *Modul:* NitroPDF.exe

  - Panel

### Grup `FitActualSize`

- *Modul:* NitroPDF.exe

  - Btn

### Grup `FolderLevel`

- *Modul:* np_smart_tips.dll

  - Btn

### Grup `Format`

- *Modul:* np_annotations.dll

  - TextEditing › SelectLines
  - TextEditing › SelectParagraphs

### Grup `FormsTool`

- *Modul:* np_forms.dll

  - AlignBottom › Btn
  - AlignHorizontally › Btn
  - AlignLeft › Btn
  - AlignRight › Btn
  - AlignTop › Btn
  - AlignVertically › Btn
  - Appearance › Btn
  - BorderColor › Btn
  - CenterBoth › Btn
  - CenterHorizontally › Btn
  - CenterVertically › Btn
  - DistributeHorizontally › Btn
  - DistributeVertically › Btn
  - FillColor › Btn
  - HorizontalSpacingLower › Btn
  - HorizontalSpacingRaise › Btn
  - InheritProperties › Btn
  - LineThickness › Btn
  - MakeCopies › Btn
  - Name › Combo
  - Properties › Btn
  - ReadOnly › Btn
  - Required › Btn
  - Rotate › Btn
  - SetAsDefault › Btn
  - SizeBoth › Btn
  - SizeHeight › Btn
  - SizeWidth › Btn
  - VerticalSpacingLower › Btn
  - VerticalSpacingRaise › Btn
  - VisibleOnScreen › Btn
  - VisibleWhenPrinted › Btn

### Grup `FromClipboard`

- *Modul:* np_create_pdf.dll

  - Btn

### Grup `FromFile`

- *Modul:* NitroPDF.exe, np_create_pdf.dll

  - Btn

### Grup `FromScanner`

- *Modul:* np_scan2pdf.dll

  - Btn
  - CreateScanProfile › Btn
  - ManageScanProfiles › Btn
  - Profile
  - SingleScan › Btn

### Grup `General`

- *Modul:* np_forms.dll

### Grup `HeaderFooter`

- *Modul:* np_smart_tips.dll, np_watermarks.dll

  - Btn
  - Menu › EditHeaders
  - Menu › ManageHeaders
  - Menu › ManageProfiles
  - Menu › RemoveHeaders
  - Profile › %s › Btn

### Grup `HighlightText`

- *Modul:* np_annotations.dll

  - Btn

### Grup `HorizontalSpacing`

- *Modul:* np_annotations.dll, np_forms.dll, np_links.dll, np_objects.dll

### Grup `Hyperlink`

- *Modul:* np_nitro_sign.dll

  - Btn

### Grup `ImageToolsCRC`

- *Modul:* np_objects.dll

  - Adjust
  - Adjust › BrightAndContr
  - Adjust › Color
  - Adjust › Color › CMYK
  - Adjust › Color › GRAY
  - Adjust › Color › RGB
  - Adjust › Extract
  - Adjust › Properties
  - Adjust › Replace
  - Adjust › Resolution
  - Adjust › Resolution › Custom
  - Adjust › Resolution › Email
  - Adjust › Resolution › Print
  - Adjust › Resolution › Screen
  - Adjust › Resolution › Separator
  - Arrange
  - Arrange › BringToFront
  - Arrange › Flip
  - Arrange › FlipH
  - Arrange › FlipV
  - Arrange › Rotate
  - Arrange › Rotate › 180
  - Arrange › Rotate › L
  - Arrange › Rotate › R
  - Arrange › SendToBack
  - EditOAngle
  - Format
  - ObjectTCoorX
  - ObjectTCoorY
  - Size
  - Size › Crop
  - Size › Crop › DummyVertSeparator1
  - Size › Crop › DummyVertSeparator2
  - Size › Crop › DummyVertSeparator3
  - Size › Crop › DummyVertSeparator4
  - Size › Crop › DummyVertSeparator5
  - Size › Height
  - Size › LockProperties
  - Size › Scale
  - Size › Width

### Grup `ImgFromClipboard`

- *Modul:* np_objects.dll

  - Btn

### Grup `ImgFromFile`

- *Modul:* np_objects.dll

  - Btn

### Grup `ImgFromScanner`

- *Modul:* np_objects.dll

  - Btn

### Grup `ImportComments`

- *Modul:* np_annotations.dll

  - Btn

### Grup `JavaScript`

- *Modul:* np_annotations.dll

  - Sep

### Grup `Landscape`

- *Modul:* np_page_edit.dll

  - Btn

### Grup `Licensing`

- *Modul:* NitroPDF.exe

### Grup `Line`

- *Modul:* np_annotations.dll

  - Btn

### Grup `Link`

- *Modul:* np_links.dll, np_smart_tips.dll

  - Btn

### Grup `LinkAlignment`

- *Modul:* np_links.dll

### Grup `LinksTool`

- *Modul:* np_links.dll

  - AlignBottom › Btn
  - AlignHorizontally › Btn
  - AlignLeft › Btn
  - AlignRight › Btn
  - AlignTop › Btn
  - AlignVertically › Btn
  - CenterBoth › Btn
  - CenterHorizontally › Btn
  - CenterVertically › Btn
  - DistributeHorizontally › Btn
  - DistributeVertically › Btn
  - HorizontalSpacingLower › Btn
  - HorizontalSpacingRaise › Btn
  - SizeBoth › Btn
  - SizeHeight › Btn
  - SizeWidth › Btn
  - VerticalSpacingLower › Btn
  - VerticalSpacingRaise › Btn

### Grup `Main`

- *Modul:* NitroPDF.exe, np_attachments.dll, np_cloud_storage.dll, np_commands.dll, np_nitro_sign.dll, np_optimizer.dll

  - BatchProcessing › Btn
  - Close › Btn
  - Exit › Btn
  - Home › Btn
  - Info › Btn
  - New › Btn
  - Open › Btn
  - Preferences › Btn
  - Print › Btn
  - PrintBatch › Btn
  - Properties › Btn
  - Save › Btn
  - SaveAs › Btn
  - Sep1 › Sep

### Grup `MakeCopiesEveryPage`

- *Modul:* np_annotations.dll, np_forms.dll

### Grup `MakeCopiesSameName`

- *Modul:* np_annotations.dll, np_forms.dll

### Grup `MakeCopiesSpacing`

- *Modul:* np_annotations.dll, np_forms.dll

### Grup `MouseMode`

- *Modul:* NitroPDF.exe

  - Btn

### Grup `NewBookmark`

- *Modul:* np_bookmarks.dll

  - Btn

### Grup `NewLink`

- *Modul:* np_links.dll

  - Btn

### Grup `NitroCloud`

- *Modul:* NitroPDF.exe, np_nitro_sign.dll, np_smart_tips.dll

  - Documents › Btn
  - LearnMore › Btn
  - ManageAccount › Btn
  - RequestSignature › Btn
  - Share › Btn

### Grup `NitroTextEditing`

- *Modul:* np_annotations.dll

  - Center › Btn
  - Finish › Btn
  - FontCase › Btn
  - FontColor › Btn
  - FontRestriction › Embed
  - FontRestriction › Subset
  - FontSize › Combo
  - FontSpacing › Character
  - FontSpacing › Line
  - FontSpacing › Word
  - Fontname › Combo
  - Justify › Btn
  - Left › Btn
  - Right › Btn
  - TypeTextAlignmentTool › Check

### Grup `OCR`

- *Modul:* NitroPDF.exe, np_ocr.dll, np_page_edit.dll

  - Btn

### Grup `ObjectAlignment`

- *Modul:* np_objects.dll

### Grup `ObjectTool`

- *Modul:* np_objects.dll

  - AlignBottom › Btn
  - AlignHorizontally › Btn
  - AlignLeft › Btn
  - AlignRight › Btn
  - AlignTop › Btn
  - AlignVertically › Btn
  - CenterBoth › Btn
  - CenterHorizontally › Btn
  - CenterVertically › Btn
  - DistributeHorizontally › Btn
  - DistributeVertically › Btn
  - HorizontalSpacingLower › Btn
  - HorizontalSpacingRaise › Btn
  - ObjectsAlignmentTool › Check
  - SizeBoth › Btn
  - SizeHeight › Btn
  - SizeWidth › Btn
  - VerticalSpacingLower › Btn
  - VerticalSpacingRaise › Btn

### Grup `OriginalpagesizeCrop`

- *Modul:* np_page_edit.dll

  - Btn

### Grup `Oval`

- *Modul:* np_annotations.dll

  - Btn

### Grup `PDFA`

- *Modul:* np_smart_tips.dll

  - PDF-A-1b_Btn
  - PDF-A-2b_Btn
  - PDF-A-3b_Btn

### Grup `Panels`

- *Modul:* np_annotations.dll, np_forms.dll, np_links.dll, np_objects.dll

  - Align
  - Center
  - Distribute
  - General
  - More
  - Options
  - Size
  - Spacing
  - Tasks

### Grup `Pencil`

- *Modul:* np_annotations.dll

  - Btn

### Grup `PencilEraser`

- *Modul:* np_annotations.dll

  - Btn

### Grup `Perimeter`

- *Modul:* np_annotations.dll

  - Btn

### Grup `Polygon`

- *Modul:* np_annotations.dll

  - Btn

### Grup `PolygonLine`

- *Modul:* np_annotations.dll

  - Btn

### Grup `Portrait`

- *Modul:* np_page_edit.dll

  - Btn

### Grup `Properties`

- *Modul:* np_annotations.dll, np_forms.dll

### Grup `Rectangle`

- *Modul:* np_annotations.dll

  - Btn

### Grup `Redo`

- *Modul:* NitroPDF.exe

  - Btn

### Grup `RemoveAppearance`

- *Modul:* np_annotations.dll, np_forms.dll

### Grup `RenameAppearance`

- *Modul:* np_annotations.dll, np_forms.dll

### Grup `ReplaceText`

- *Modul:* np_annotations.dll, np_smart_tips.dll

  - Btn

### Grup `ResetRotation`

- *Modul:* np_forms.dll

### Grup `ReviewTool`

- *Modul:* np_annotations.dll

  - AlignBottom › Btn
  - AlignHorizontally › Btn
  - AlignLeft › Btn
  - AlignRight › Btn
  - AlignTop › Btn
  - AlignVertically › Btn
  - Center › Btn
  - CenterBoth › Btn
  - CenterHorizontally › Btn
  - CenterVertically › Btn
  - DistributeHorizontally › Btn
  - DistributeVertically › Btn
  - Finish › Btn
  - FontCase › Btn
  - FontColor › Btn
  - FontSize › Combo
  - HorizontalSpacingLower › Btn
  - HorizontalSpacingRaise › Btn
  - Left › Btn
  - Right › Btn
  - SizeBoth › Btn
  - SizeHeight › Btn
  - SizeWidth › Btn
  - Spacing › Character
  - Spacing › Line
  - Spacing › Word
  - Typewriter › Fontname › Combo
  - VerticalSpacingLower › Btn
  - VerticalSpacingRaise › Btn

### Grup `Rotate`

- *Modul:* np_forms.dll

### Grup `RotateLeft`

- *Modul:* np_forms.dll

### Grup `RotateRight`

- *Modul:* np_forms.dll

### Grup `SaveNewAppearance`

- *Modul:* np_annotations.dll, np_forms.dll

### Grup `ScannerSeparator`

- *Modul:* np_scan2pdf.dll

### Grup `Scripting`

- *Modul:* NitroPDF.exe

### Grup `Stamp`

- *Modul:* np_stamper.dll

  - CreateNewStamp › Btn
  - ManageStamps › Btn

### Grup `StampSignature`

- *Modul:* np_signature_stamp.dll

  - CreateNewSignature › Btn
  - ManageSignatures › Btn

### Grup `SummarizeCommentsAndPrint`

- *Modul:* np_annotations.dll

### Grup `TextBox`

- *Modul:* np_annotations.dll, np_smart_tips.dll

  - Btn

### Grup `Tools`

- *Modul:* np_forms.dll

  - Panel

### Grup `ToolsFP`

- *Modul:* NitroPDF.exe, np_annotations.dll, np_attachments.dll, np_bookmarks.dll, np_compare_pdf.dll, np_convert_pdf.dll, np_create_pdf.dll, np_digital_signature.dll, np_forms.dll, np_java_script_deprecated.dll, np_javascript.dll, np_links.dll, np_nitro_sign.dll, np_objects.dll, np_ocr.dll, np_page_edit.dll, np_pdfa.dll, np_redaction.dll, np_scan2pdf.dll, np_set_security.dll, np_stamper.dll, np_watermarks.dll

### Grup `TouchMode`

- *Modul:* NitroPDF.exe

  - Btn

### Grup `TouchMouseMode`

- *Modul:* NitroPDF.exe

  - Btn

### Grup `UnderlineText`

- *Modul:* np_annotations.dll, np_smart_tips.dll

  - Btn

### Grup `Undo`

- *Modul:* NitroPDF.exe

  - Btn

### Grup `UpdateAppearance`

- *Modul:* np_annotations.dll, np_forms.dll

### Grup `VerticalSpacing`

- *Modul:* np_annotations.dll, np_forms.dll, np_links.dll, np_objects.dll

### Grup `View`

- *Modul:* NitroPDF.exe

  - FitPage › Btn
  - FitWidth › Btn
  - Hand › Btn
  - ZoomTool › Btn

### Grup `Watermark`

- *Modul:* np_smart_tips.dll, np_watermarks.dll

  - Btn

### Grup `Watermarks`

- *Modul:* np_watermarks.dll

  - Menu › EditWatermarks
  - Menu › ManageProfiles
  - Menu › ManageWatermarks
  - Menu › RemoveWatermarks
  - Profile › %s › Btn

### Grup `Zoom`

- *Modul:* NitroPDF.exe

  - Sep

### Grup `Zoom100`

- *Modul:* NitroPDF.exe

  - Btn

### Grup `Zoom125`

- *Modul:* NitroPDF.exe

  - Btn

### Grup `Zoom150`

- *Modul:* NitroPDF.exe

  - Btn

### Grup `Zoom1600`

- *Modul:* NitroPDF.exe

  - Btn

### Grup `Zoom200`

- *Modul:* NitroPDF.exe

  - Btn

### Grup `Zoom25`

- *Modul:* NitroPDF.exe

  - Btn

### Grup `Zoom400`

- *Modul:* NitroPDF.exe

  - Btn

### Grup `Zoom50`

- *Modul:* NitroPDF.exe

  - Btn

### Grup `Zoom75`

- *Modul:* NitroPDF.exe

  - Btn

### Grup `Zoom800`

- *Modul:* NitroPDF.exe

  - Btn

### Grup `ZoomIn`

- *Modul:* NitroPDF.exe

  - Btn

### Grup `ZoomOut`

- *Modul:* NitroPDF.exe

  - Btn

## Tab `Home`

### Grup `(langsung)`

- *Modul:* np_annotations.dll, np_convert_pdf.dll, np_create_pdf.dll, np_nitro_sign.dll, np_objects.dll, np_page_edit.dll, np_scan2pdf.dll, np_signature_stamp.dll, np_smart_tips.dll

### Grup `AddTools`

- *Modul:* NitroPDF.exe

  - Btn

### Grup `Advanced`

- *Modul:* np_page_edit.dll

### Grup `Combine`

- *Modul:* NitroPDF.exe, np_create_pdf.dll

  - Btn

### Grup `Convert`

- *Modul:* NitroPDF.exe, np_annotations.dll, np_convert_pdf.dll, np_page_edit.dll

  - ToExcel › Btn
  - ToWord › Btn

### Grup `Create`

- *Modul:* np_annotations.dll, np_convert_pdf.dll, np_create_pdf.dll, np_page_edit.dll, np_scan2pdf.dll

### Grup `Delete`

- *Modul:* np_page_edit.dll

### Grup `Document`

- *Modul:* NitroPDF.exe

### Grup `Edit`

- *Modul:* NitroPDF.exe, np_objects.dll

### Grup `Extract`

- *Modul:* np_page_edit.dll

### Grup `Find`

- *Modul:* NitroPDF.exe

### Grup `Insert`

- *Modul:* np_page_edit.dll

### Grup `InsertBlankPage`

- *Modul:* np_page_edit.dll

### Grup `InsertFromClipboard`

- *Modul:* np_page_edit.dll

### Grup `InsertFromFile`

- *Modul:* np_page_edit.dll

### Grup `InsertFromScanner`

- *Modul:* np_page_edit.dll

### Grup `Left`

- *Modul:* np_page_edit.dll

### Grup `PDF`

- *Modul:* np_create_pdf.dll, np_scan2pdf.dll

  - Btn

### Grup `PageLayout`

- *Modul:* np_page_edit.dll

### Grup `Portfolio`

- *Modul:* np_attachments.dll, np_smart_tips.dll

  - Btn

### Grup `Review`

- *Modul:* NitroPDF.exe, np_annotations.dll, np_page_edit.dll

### Grup `Right`

- *Modul:* np_page_edit.dll

### Grup `Rotate`

- *Modul:* np_page_edit.dll

### Grup `Select`

- *Modul:* NitroPDF.exe

### Grup `SelectTextAndGraphic`

- *Modul:* NitroPDF.exe

### Grup `Snapshot`

- *Modul:* NitroPDF.exe

### Grup `StampSignature`

- *Modul:* NitroPDF.exe, np_signature_stamp.dll

  - Btn

### Grup `TemporarilyRotateView`

- *Modul:* np_page_edit.dll

### Grup `Tools`

- *Modul:* NitroPDF.exe, np_annotations.dll, np_convert_pdf.dll, np_create_pdf.dll, np_nitro_sign.dll, np_page_edit.dll, np_scan2pdf.dll, np_signature_stamp.dll

### Grup `TypeText`

- *Modul:* np_annotations.dll

  - Btn

## Tab `Protect`

### Grup `(langsung)`

- *Modul:* NitroPDF.exe, np_annotations.dll, np_digital_signature.dll, np_objects.dll, np_redaction.dll, np_set_security.dll

### Grup `ApplyAllRedactions`

- *Modul:* np_redaction.dll

### Grup `CertificateSecurity`

- *Modul:* np_set_security.dll

  - Btn
  - Btn › %d

### Grup `CertifyDocument`

- *Modul:* np_digital_signature.dll, np_set_security.dll

### Grup `DigSig`

- *Modul:* np_digital_signature.dll

  - Certify › Btn
  - Sign › Btn

### Grup `Identification`

- *Modul:* np_set_security.dll

### Grup `MSSecurity`

- *Modul:* np_set_security.dll, np_smart_tips.dll

  - Btn

### Grup `ManageProfiles`

- *Modul:* np_set_security.dll

  - Btn

### Grup `MarkForRedaction`

- *Modul:* np_redaction.dll, np_smart_tips.dll

### Grup `MarkPages`

- *Modul:* np_redaction.dll

### Grup `MyDigitalID`

- *Modul:* np_set_security.dll

  - Btn

### Grup `PasswordSecurity`

- *Modul:* NitroPDF.exe, np_set_security.dll

  - Btn
  - Btn › %d

### Grup `RMSSecurity`

- *Modul:* np_smart_tips.dll

  - Btn

### Grup `Redact`

- *Modul:* np_digital_signature.dll, np_redaction.dll, np_set_security.dll

### Grup `RedactionProperties`

- *Modul:* np_redaction.dll

### Grup `RemoveMetadata`

- *Modul:* np_redaction.dll

### Grup `RepeatMarkAcrossPages`

- *Modul:* np_redaction.dll

### Grup `SearchAndRedact`

- *Modul:* np_redaction.dll

### Grup `SecureDocument`

- *Modul:* np_digital_signature.dll, np_set_security.dll

### Grup `Sensitivity`

- *Modul:* np_digital_signature.dll, np_set_security.dll

### Grup `TrustedContacts`

- *Modul:* np_set_security.dll

  - Btn

## Tab `Forms`

### Grup `(langsung)`

- *Modul:* NitroPDF.exe, np_convert_pdf.dll, np_forms.dll, np_javascript.dll, np_objects.dll

### Grup `AutoForm`

- *Modul:* np_convert_pdf.dll, np_forms.dll

  - CreateForms › Btn

### Grup `BarcodeField`

- *Modul:* np_forms.dll

  - Btn

### Grup `CheckBox`

- *Modul:* np_forms.dll, np_smart_tips.dll

  - Btn

### Grup `ComboBox`

- *Modul:* np_forms.dll

  - Btn

### Grup `DigitalSignature`

- *Modul:* np_forms.dll

  - Btn

### Grup `DocumentSetup`

- *Modul:* np_forms.dll, np_java_script_deprecated.dll, np_javascript.dll

### Grup `EditAllFields`

- *Modul:* np_forms.dll, np_smart_tips.dll

  - Btn

### Grup `Export`

- *Modul:* np_forms.dll

  - Btn

### Grup `FormData`

- *Modul:* np_forms.dll, np_java_script_deprecated.dll, np_javascript.dll

### Grup `FormFields`

- *Modul:* np_convert_pdf.dll, np_forms.dll, np_java_script_deprecated.dll, np_javascript.dll

### Grup `Import`

- *Modul:* np_forms.dll

  - Btn

### Grup `ListBox`

- *Modul:* np_forms.dll

  - Btn

### Grup `PushButton`

- *Modul:* np_forms.dll

  - Btn

### Grup `RadioButton`

- *Modul:* np_forms.dll

  - Btn

### Grup `ResetForm`

- *Modul:* np_forms.dll

  - Btn

### Grup `SetCalculationOrder`

- *Modul:* np_forms.dll

  - Btn

### Grup `SetTabOrder`

- *Modul:* np_forms.dll, np_smart_tips.dll

  - Btn

### Grup `ShowGrid`

- *Modul:* NitroPDF.exe

  - Check

### Grup `SnapToGrid`

- *Modul:* NitroPDF.exe

  - Check

### Grup `TextField`

- *Modul:* np_forms.dll, np_smart_tips.dll

  - Btn

### Grup `View`

- *Modul:* NitroPDF.exe

## Tab `Review`

### Grup `(langsung)`

- *Modul:* NitroPDF.exe, np_annotations.dll, np_compare_pdf.dll, np_objects.dll, np_ocr.dll, np_stamper.dll

### Grup `AddNote`

- *Modul:* NitroPDF.exe, np_annotations.dll, np_smart_tips.dll

  - Btn

### Grup `AttachFiles`

- *Modul:* np_annotations.dll, np_smart_tips.dll

  - Btn

### Grup `AutoDeskewDoc`

- *Modul:* np_ocr.dll

  - Btn

### Grup `Comments`

- *Modul:* np_annotations.dll

### Grup `ContentComparePDF`

- *Modul:* np_compare_pdf.dll, np_smart_tips.dll

  - Btn

### Grup `ContextAligment`

- *Modul:* np_annotations.dll

### Grup `ContextAppearance`

- *Modul:* np_annotations.dll

### Grup `Document`

- *Modul:* np_annotations.dll, np_compare_pdf.dll, np_ocr.dll

### Grup `Drawing`

- *Modul:* np_annotations.dll, np_objects.dll, np_smart_tips.dll

  - Btn

### Grup `HideComments`

- *Modul:* np_annotations.dll

  - Btn

### Grup `Markup`

- *Modul:* NitroPDF.exe, np_annotations.dll, np_compare_pdf.dll, np_objects.dll, np_ocr.dll, np_stamper.dll

### Grup `Measure`

- *Modul:* np_annotations.dll, np_smart_tips.dll

  - Btn

### Grup `Migrate`

- *Modul:* np_annotations.dll

  - Btn

### Grup `ReviewTools`

- *Modul:* np_annotations.dll, np_compare_pdf.dll, np_objects.dll, np_ocr.dll, np_stamper.dll

### Grup `Select`

- *Modul:* NitroPDF.exe

### Grup `SelectTextAndGraphic`

- *Modul:* NitroPDF.exe

### Grup `Shapes`

- *Modul:* NitroPDF.exe, np_annotations.dll, np_objects.dll, np_smart_tips.dll

  - Btn

### Grup `Snapsjot`

- *Modul:* NitroPDF.exe

### Grup `Stamp`

- *Modul:* NitroPDF.exe, np_annotations.dll, np_objects.dll, np_smart_tips.dll, np_stamper.dll

  - Btn

### Grup `SummarizeComments`

- *Modul:* np_annotations.dll

  - Btn

## Tab `PageLayout`

### Grup `(langsung)`

- *Modul:* NitroPDF.exe, np_bookmarks.dll, np_links.dll, np_objects.dll, np_ocr.dll, np_page_edit.dll, np_stamper.dll, np_watermarks.dll

### Grup `Advanced`

- *Modul:* np_page_edit.dll

### Grup `Crop`

- *Modul:* np_page_edit.dll

### Grup `Delete`

- *Modul:* np_page_edit.dll

### Grup `Document`

- *Modul:* np_ocr.dll

### Grup `Extract`

- *Modul:* np_page_edit.dll

### Grup `Insert`

- *Modul:* np_page_edit.dll

### Grup `InsertBlankPage`

- *Modul:* np_page_edit.dll

### Grup `InsertFromClipboard`

- *Modul:* np_page_edit.dll

### Grup `InsertFromFile`

- *Modul:* np_page_edit.dll

### Grup `InsertFromScanner`

- *Modul:* np_page_edit.dll

### Grup `Left`

- *Modul:* np_page_edit.dll

### Grup `Navigation`

- *Modul:* np_bookmarks.dll, np_links.dll, np_ocr.dll

### Grup `PageMarks`

- *Modul:* np_bookmarks.dll, np_links.dll, np_ocr.dll, np_stamper.dll, np_watermarks.dll

### Grup `Pages`

- *Modul:* np_bookmarks.dll, np_links.dll, np_ocr.dll, np_page_edit.dll, np_stamper.dll, np_watermarks.dll

### Grup `Replace`

- *Modul:* np_page_edit.dll, np_smart_tips.dll

### Grup `Right`

- *Modul:* np_page_edit.dll

### Grup `Rotate`

- *Modul:* np_page_edit.dll

### Grup `Split`

- *Modul:* np_page_edit.dll, np_smart_tips.dll

### Grup `TemporarilyRotateView`

- *Modul:* np_page_edit.dll

## Tab `Help`

### Grup `(langsung)`

- *Modul:* NitroPDF.exe, np_objects.dll

### Grup `About`

- *Modul:* NitroPDF.exe

  - Btn

### Grup `Activate`

- *Modul:* NitroPDF.exe

### Grup `Activation`

- *Modul:* NitroPDF.exe

### Grup `CheckForUpdates`

- *Modul:* NitroPDF.exe

### Grup `CommunitySupport`

- *Modul:* NitroPDF.exe

  - Btn

### Grup `ContactSupport`

- *Modul:* NitroPDF.exe

  - Btn

### Grup `Help`

- *Modul:* NitroPDF.exe

### Grup `KnowledgeBase`

- *Modul:* NitroPDF.exe

  - Btn

### Grup `LearningCenter`

- *Modul:* NitroPDF.exe

  - Btn

### Grup `OnlineSupport`

- *Modul:* NitroPDF.exe

### Grup `Product`

- *Modul:* NitroPDF.exe

### Grup `ReportAProblem`

- *Modul:* NitroPDF.exe

  - Btn

### Grup `SupportTools`

- *Modul:* NitroPDF.exe

  - Btn

### Grup `UserGuide`

- *Modul:* NitroPDF.exe

  - Btn

### Grup `VolumeLicensing`

- *Modul:* NitroPDF.exe

  - Btn

## Tab `Convert`

### Grup `(langsung)`

- *Modul:* NitroPDF.exe, np_attachments.dll, np_convert_pdf.dll, np_objects.dll, np_pdfa.dll

### Grup `Create`

- *Modul:* np_attachments.dll

### Grup `Extract`

- *Modul:* np_attachments.dll, np_convert_pdf.dll

  - ExtractForms › Btn
  - ExtractTables › Btn

### Grup `ExtractImages`

- *Modul:* np_convert_pdf.dll, np_smart_tips.dll

  - Btn

### Grup `Formats`

- *Modul:* np_attachments.dll, np_convert_pdf.dll, np_pdfa.dll

  - PDFA › Btn
  - ToExcel › Btn
  - ToWord › Btn

### Grup `ToImage`

- *Modul:* np_convert_pdf.dll, np_smart_tips.dll

  - Btn

### Grup `ToPPTX`

- *Modul:* np_convert_pdf.dll

  - Btn

### Grup `ToPlainText`

- *Modul:* np_convert_pdf.dll, np_smart_tips.dll

  - Btn

### Grup `ToRichText`

- *Modul:* np_convert_pdf.dll, np_smart_tips.dll

  - Btn

## Tab `Erase`

### Grup `(langsung)`

- *Modul:* NitroPDF.exe, np_objects.dll, np_redaction.dll

### Grup `ApplyAllRedactions`

- *Modul:* np_redaction.dll, np_smart_tips.dll

### Grup `MarkForRedaction`

- *Modul:* np_redaction.dll, np_smart_tips.dll

### Grup `MarkPages`

- *Modul:* np_redaction.dll

### Grup `Mask`

- *Modul:* np_redaction.dll

### Grup `Redact`

- *Modul:* np_redaction.dll

### Grup `RedactionProperties`

- *Modul:* np_redaction.dll

### Grup `RemoveMetadata`

- *Modul:* np_redaction.dll, np_smart_tips.dll

### Grup `RepeatMarkAcrossPages`

- *Modul:* np_redaction.dll

### Grup `SearchAndRedact`

- *Modul:* np_redaction.dll, np_smart_tips.dll

### Grup `Security`

- *Modul:* np_redaction.dll

### Grup `Whiteout`

- *Modul:* NitroPDF.exe, np_redaction.dll, np_smart_tips.dll

## Tab `Share`

### Grup `(langsung)`

- *Modul:* NitroPDF.exe, np_nitro_sign.dll, np_objects.dll

### Grup `Email`

- *Modul:* NitroPDF.exe, np_nitro_sign.dll

### Grup `EmailAsAttachment`

- *Modul:* NitroPDF.exe, np_smart_tips.dll

### Grup `NitroSign`

- *Modul:* np_nitro_sign.dll

## Tab `Accessibility`

### Grup `(langsung)`

- *Modul:* NitroPDF.exe, np_accessibility.dll

## Tab `BackStage`

### Grup `(langsung)`

- *Modul:* NitroPDF.exe

## Tab `Favorite`

### Grup `(langsung)`

- *Modul:* NitroPDF.exe, np_objects.dll

## Tab `IManage`

### Grup `(langsung)`

- *Modul:* NitroPDF.exe
