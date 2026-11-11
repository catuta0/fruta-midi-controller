// Render or extract text of PDF pages using macOS PDFKit. Usage:
// swift pdfpages.swift <pdf> <outdir> <dpi> <page,page,...|text>
import Foundation
import PDFKit
import AppKit

let a = CommandLine.arguments
guard a.count >= 5, let doc = PDFDocument(url: URL(fileURLWithPath: a[1])) else { print("open failed"); exit(1) }
let outdir = a[2]
let dpi = CGFloat(Double(a[3]) ?? 200)
print("pages", doc.pageCount)
if a[4] == "text" {
    var out = ""
    for i in 0..<doc.pageCount {
        out += "=== PAGE \(i + 1) ===\n" + (doc.page(at: i)?.string ?? "") + "\n"
    }
    let name = URL(fileURLWithPath: a[1]).deletingPathExtension().lastPathComponent
    try out.write(toFile: outdir + "/" + name + ".txt", atomically: true, encoding: .utf8)
    print("text ok")
    exit(0)
}
for s in a[4].split(separator: ",") {
    guard let n = Int(s), let page = doc.page(at: n - 1) else { continue }
    let box = page.bounds(for: .mediaBox)
    let scale = dpi / 72.0
    let w = Int(box.width * scale), h = Int(box.height * scale)
    let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: w, pixelsHigh: h, bitsPerSample: 8, samplesPerPixel: 4,
                               hasAlpha: true, isPlanar: false, colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
    let ctx = NSGraphicsContext(bitmapImageRep: rep)!
    NSGraphicsContext.current = ctx
    ctx.cgContext.setFillColor(CGColor(red: 1, green: 1, blue: 1, alpha: 1))
    ctx.cgContext.fill(CGRect(x: 0, y: 0, width: w, height: h))
    ctx.cgContext.scaleBy(x: scale, y: scale)
    page.draw(with: .mediaBox, to: ctx.cgContext)
    ctx.flushGraphics()
    let png = rep.representation(using: .png, properties: [:])!
    try png.write(to: URL(fileURLWithPath: outdir + "/p\(n).png"))
    print("wrote p\(n).png", w, h)
}
