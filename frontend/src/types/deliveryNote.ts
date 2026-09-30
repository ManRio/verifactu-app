export type DeliveryNoteStatus = 'DRAFT' | 'CONFIRMED' | 'CANCELLED';

export type DeliveryNoteLine = {
  id: number;
  delivery_note_id: number;
  order_line_id: number;
  description: string;
  quantity: string;
  unit_price: string;
  tax_rate: string;
  position: number;
  created_at: string;
};

export type DeliveryNote = {
  id: number;
  business_id: number;
  order_id: number;
  status: DeliveryNoteStatus;
  delivery_date: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
  confirmed_at: string | null;
  lines: DeliveryNoteLine[];
};

export type DeliveryNoteLineInput = {
  order_line_id: number;
  quantity: string;
  position: number;
};
