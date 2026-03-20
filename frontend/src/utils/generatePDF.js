import jsPDF from 'jspdf'
import autoTable from 'jspdf-autotable'

/* ── Brand colours ── */
const C = {
  indigo:      [99,  102, 241],
  indigoDark:  [67,  56,  202],
  violet:      [139, 92,  246],
  dark:        [13,  17,  23],
  white:       [255, 255, 255],
  slate100:    [241, 245, 249],
  slate200:    [226, 232, 240],
  slate500:    [100, 116, 139],
  slate700:    [51,  65,  85],
  slate900:    [15,  23,  42],
  green:       [16,  185, 129],
  red:         [239, 68,  68],
  yellow:      [245, 158, 11],
  amber:       [251, 191, 36],
}

/* ── Helpers ── */
const hex = ([r, g, b]) => ({ r, g, b })

function setFill(doc, color)   { doc.setFillColor(...color) }
function setFont(doc, color)   { doc.setTextColor(...color) }
function setDraw(doc, color)   { doc.setDrawColor(...color) }

function fmt(n, prefix = '$') {
  return prefix + parseFloat(n || 0).toFixed(2)
}

function periodLabel(period) {
  return { week: 'Last 7 Days', month: 'Last 30 Days', year: 'Last 12 Months' }[period] || period
}

function statusColor(status) {
  switch(status) {
    case 'picked_up':  return [16, 185, 129]
    case 'preparing':  return [249, 115, 22]
    case 'confirmed':  return [96, 165, 250]
    case 'ready':      return [52, 211, 153]
    case 'cancelled':  return [239, 68, 68]
    default:           return [245, 158, 11]  // new
  }
}

function payBadgeColor(status) {
  return status === 'paid' ? [16, 185, 129] : [100, 116, 139]
}

/* ── Main export function ── */
export async function generateReportPDF(data) {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
  const PW  = doc.internal.pageSize.getWidth()   // 210
  const PH  = doc.internal.pageSize.getHeight()  // 297
  const M   = 14   // margin

  let y = 0  // current Y cursor

  /* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     PAGE 1 — COVER HEADER
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

  // Dark header band
  setFill(doc, C.dark)
  doc.rect(0, 0, PW, 52, 'F')

  // Indigo accent stripe
  setFill(doc, C.indigo)
  doc.rect(0, 52, PW, 3, 'F')

  // Restaurant name
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(22)
  setFont(doc, C.white)
  doc.text(data.restaurant_name?.toUpperCase() || 'RESTAURANT', M, 22)

  // Report subtitle
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(10)
  setFont(doc, [165, 180, 252])  // indigo-300
  doc.text('AI AGENT  •  BUSINESS REPORT', M, 31)

  // Period pill (right side)
  const pillLabel = periodLabel(data.period)
  doc.setFontSize(9)
  doc.setFont('helvetica', 'bold')
  setFill(doc, C.indigo)
  doc.roundedRect(PW - M - 44, 14, 44, 10, 2, 2, 'F')
  setFont(doc, C.white)
  doc.text(pillLabel, PW - M - 22, 20.5, { align: 'center' })

  // Date range line
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(8.5)
  setFont(doc, [148, 163, 184])  // slate-400
  const since = new Date(data.since).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  const until = new Date(data.until).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  doc.text(`${since}  →  ${until}`, M, 41)

  // Generated timestamp
  const genAt = new Date().toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' })
  doc.text(`Generated: ${genAt}`, PW - M, 41, { align: 'right' })

  y = 65

  /* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     SECTION 1 — ORDER SUMMARY METRICS
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

  sectionHeader(doc, 'Order Summary', y, M, PW)
  y += 8

  const s = data.summary
  const metrics = [
    { label: 'Total Orders',     value: String(s.total_orders),            color: C.indigo },
    { label: 'Completed',        value: String(s.completed_orders),         color: C.green  },
    { label: 'Cancelled',        value: String(s.cancelled_orders),         color: C.red    },
    { label: 'Total Revenue',    value: fmt(s.revenue),                     color: C.indigo },
    { label: 'Avg Order Value',  value: fmt(s.avg_order_value),             color: C.violet },
    { label: 'Completion Rate',  value: s.total_orders
        ? Math.round(s.completed_orders / s.total_orders * 100) + '%'
        : '—',                                                              color: C.green  },
  ]

  drawMetricGrid(doc, metrics, y, M, PW, 3)
  y += 30

  /* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     SECTION 2 — CALL ANALYTICS
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

  sectionHeader(doc, 'AI Call Analytics', y, M, PW)
  y += 8

  const c = data.calls
  const callMetrics = [
    { label: 'Total Calls',       value: String(c.total),                   color: C.indigo },
    { label: 'Completed Calls',   value: String(c.completed),               color: C.green  },
    { label: 'Abandoned',         value: String(c.abandoned),               color: C.red    },
    { label: 'Completion Rate',   value: c.completion_rate + '%',           color: c.completion_rate >= 80 ? C.green : C.yellow },
    { label: 'Avg Call Duration', value: formatDuration(c.avg_duration_seconds), color: C.violet },
    { label: 'Orders from Calls', value: String(s.total_orders),            color: C.indigo },
  ]

  drawMetricGrid(doc, callMetrics, y, M, PW, 3)
  y += 30

  /* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     SECTION 3 — CALLS BY DATE TABLE
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

  sectionHeader(doc, 'Daily Call Volume', y, M, PW)
  y += 5

  const callRows = (data.calls_by_date || []).map(d => [
    formatDate(d.date),
    d.completed || 0,
    d.abandoned  || 0,
    (d.completed || 0) + (d.abandoned || 0),
    d.completed && ((d.completed || 0) + (d.abandoned || 0))
      ? Math.round((d.completed / ((d.completed || 0) + (d.abandoned || 0))) * 100) + '%'
      : '—',
  ])

  autoTable(doc, {
    startY: y,
    head: [['Date', 'Completed', 'Abandoned', 'Total', 'Rate']],
    body: callRows,
    margin: { left: M, right: M },
    styles: {
      font: 'helvetica', fontSize: 8.5,
      cellPadding: 3.5, valign: 'middle',
      textColor: C.slate700,
    },
    headStyles: {
      fillColor: C.indigo,
      textColor: C.white,
      fontStyle: 'bold',
      fontSize: 8.5,
    },
    alternateRowStyles: { fillColor: C.slate100 },
    columnStyles: {
      0: { cellWidth: 32 },
      1: { halign: 'center', textColor: C.green },
      2: { halign: 'center', textColor: C.red   },
      3: { halign: 'center', fontStyle: 'bold'  },
      4: { halign: 'center' },
    },
    didDrawPage: (d) => { drawPageFooter(doc, PW, PH, data.restaurant_name) },
  })

  y = doc.lastAutoTable.finalY + 10

  /* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     SECTION 4 — REVENUE BY DATE TABLE
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

  if (data.revenue_by_date?.length) {
    if (y > PH - 60) { doc.addPage(); y = 20 }

    sectionHeader(doc, 'Daily Revenue', y, M, PW)
    y += 5

    const revRows = data.revenue_by_date.map(d => [
      formatDate(d.date),
      fmt(d.revenue),
    ])

    autoTable(doc, {
      startY: y,
      head: [['Date', 'Revenue']],
      body: revRows,
      margin: { left: M, right: M },
      tableWidth: 80,
      styles: {
        font: 'helvetica', fontSize: 8.5,
        cellPadding: 3.5, valign: 'middle',
        textColor: C.slate700,
      },
      headStyles: { fillColor: C.indigo, textColor: C.white, fontStyle: 'bold' },
      alternateRowStyles: { fillColor: C.slate100 },
      columnStyles: {
        0: { cellWidth: 40 },
        1: { halign: 'right', fontStyle: 'bold', textColor: C.indigo },
      },
      didDrawPage: () => { drawPageFooter(doc, PW, PH, data.restaurant_name) },
    })

    y = doc.lastAutoTable.finalY + 10
  }

  /* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     SECTION 5 — FULL ORDERS TABLE
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

  // Always start orders on a new page for readability
  doc.addPage()
  y = 20

  sectionHeader(doc, `All Orders  (${data.orders?.length || 0})`, y, M, PW)
  y += 5

  const orderRows = (data.orders || []).map((o, i) => [
    i + 1,
    o.created_at,
    o.customer_name,
    o.customer_phone,
    o.items || '—',
    fmt(o.total),
    o.status.replace('_', ' '),
    o.payment_status,
  ])

  autoTable(doc, {
    startY: y,
    head: [['#', 'Date & Time', 'Customer', 'Phone', 'Items', 'Total', 'Status', 'Payment']],
    body: orderRows,
    margin: { left: M, right: M },
    styles: {
      font: 'helvetica', fontSize: 7.5,
      cellPadding: 3, valign: 'middle',
      textColor: C.slate700, overflow: 'linebreak',
    },
    headStyles: {
      fillColor: C.dark,
      textColor: C.white,
      fontStyle: 'bold',
      fontSize: 8,
    },
    alternateRowStyles: { fillColor: C.slate100 },
    columnStyles: {
      0: { cellWidth: 7,  halign: 'center', textColor: C.slate500 },
      1: { cellWidth: 28, fontSize: 7 },
      2: { cellWidth: 24, fontStyle: 'bold' },
      3: { cellWidth: 22, fontSize: 7, textColor: C.slate500 },
      4: { cellWidth: 'auto' },
      5: { cellWidth: 17, halign: 'right', fontStyle: 'bold', textColor: C.indigoDark },
      6: { cellWidth: 20, halign: 'center' },
      7: { cellWidth: 16, halign: 'center' },
    },
    didParseCell: (hookData) => {
      // Colour-code status column
      if (hookData.column.index === 6 && hookData.section === 'body') {
        const raw = data.orders?.[hookData.row.index]?.status
        if (raw) {
          hookData.cell.styles.textColor = statusColor(raw)
          hookData.cell.styles.fontStyle = 'bold'
        }
      }
      // Colour-code payment column
      if (hookData.column.index === 7 && hookData.section === 'body') {
        const raw = data.orders?.[hookData.row.index]?.payment_status
        if (raw) hookData.cell.styles.textColor = payBadgeColor(raw)
      }
    },
    didDrawPage: () => { drawPageFooter(doc, PW, PH, data.restaurant_name) },
  })

  // Final page footer
  drawPageFooter(doc, PW, PH, data.restaurant_name)

  /* ── Save ── */
  const fname = `${(data.restaurant_name || 'report').replace(/\s+/g, '_')}_${data.period}_report_${data.until}.pdf`
  doc.save(fname)
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   HELPER COMPONENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

function sectionHeader(doc, title, y, M, PW) {
  // Accent line + label
  setFill(doc, C.indigo)
  doc.rect(M, y, 3, 5, 'F')
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(10)
  setFont(doc, C.slate900)
  doc.text(title, M + 6, y + 4)

  setDraw(doc, C.slate200)
  doc.setLineWidth(0.3)
  doc.line(M, y + 7, PW - M, y + 7)
}

function drawMetricGrid(doc, metrics, y, M, PW, cols = 3) {
  const totalW = PW - M * 2
  const cellW  = totalW / cols
  const cellH  = 22

  metrics.forEach((m, i) => {
    const col = i % cols
    const row = Math.floor(i / cols)
    const x   = M + col * cellW
    const cy  = y + row * cellH

    // Card background
    setFill(doc, C.slate100)
    doc.roundedRect(x + 1, cy, cellW - 2, cellH - 2, 2, 2, 'F')

    // Accent top border
    setFill(doc, m.color)
    doc.rect(x + 1, cy, cellW - 2, 1.5, 'F')

    // Value
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(13)
    setFont(doc, m.color)
    doc.text(m.value, x + (cellW / 2), cy + 10, { align: 'center' })

    // Label
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(7.5)
    setFont(doc, C.slate500)
    doc.text(m.label, x + (cellW / 2), cy + 16, { align: 'center' })
  })
}

function drawPageFooter(doc, PW, PH, restaurantName) {
  const totalPages = doc.internal.getNumberOfPages()
  const currentPage = doc.internal.getCurrentPageInfo().pageNumber

  setFill(doc, C.slate100)
  doc.rect(0, PH - 10, PW, 10, 'F')

  doc.setFont('helvetica', 'normal')
  doc.setFontSize(7)
  setFont(doc, C.slate500)
  doc.text(`${restaurantName} — Confidential Business Report`, 14, PH - 3.5)
  doc.text(`Page ${currentPage} of ${totalPages}`, PW - 14, PH - 3.5, { align: 'right' })
}

function formatDate(isoStr) {
  if (!isoStr) return ''
  const d = new Date(isoStr + 'T00:00:00')
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function formatDuration(seconds) {
  if (!seconds) return '—'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return m > 0 ? `${m}m ${s}s` : `${s}s`
}
