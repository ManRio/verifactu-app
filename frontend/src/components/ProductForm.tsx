import { useState } from 'react';
import type { FormEvent } from 'react';

import {
  createProduct,
  updateProduct,
  type CreateProductData,
} from '../services/product';

import type { Product } from '../types/product';

type ProductFormProps = {
  product?: Product | null;
  onSaved: (product: Product) => void;
  onCancel: () => void;
};

function ProductForm({ product, onSaved, onCancel }: ProductFormProps) {
  const [name, setName] = useState(product?.name ?? '');
  const [sku, setSku] = useState(product?.sku ?? '');
  const [description, setDescription] = useState(product?.description ?? '');
  const [unitPrice, setUnitPrice] = useState(product?.unit_price ?? '');
  const [taxRate, setTaxRate] = useState(product?.tax_rate ?? '21');

  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isEditing = product != null;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setError('');
    setIsSubmitting(true);

    const data: CreateProductData = {
      name: name.trim(),
      sku: sku.trim() || null,
      description: description.trim() || null,
      unit_price: unitPrice,
      tax_rate: taxRate,
    };

    try {
      const savedProduct = isEditing
        ? await updateProduct(product.id, data)
        : await createProduct(data);

      onSaved(savedProduct);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : `No se pudo ${isEditing ? 'actualizar' : 'crear'} el producto`,
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className='mb-8 rounded-2xl border border-slate-800 bg-slate-900 p-6'>
      <div className='mb-6'>
        <h2 className='text-xl font-semibold'>
          {isEditing ? 'Editar producto' : 'Nuevo producto'}
        </h2>

        <p className='mt-1 text-sm text-slate-400'>
          {isEditing
            ? 'Modifica los datos del producto.'
            : 'Añade un producto al catálogo de tu negocio.'}
        </p>
      </div>

      <form onSubmit={handleSubmit} className='grid gap-5 md:grid-cols-2'>
        <label className='flex flex-col gap-2'>
          <span className='text-sm font-medium'>Nombre *</span>

          <input
            type='text'
            required
            maxLength={150}
            value={name}
            onChange={(event) => setName(event.target.value)}
            className='rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-emerald-500'
          />
        </label>

        <label className='flex flex-col gap-2'>
          <span className='text-sm font-medium'>SKU</span>

          <input
            type='text'
            maxLength={50}
            value={sku}
            onChange={(event) => setSku(event.target.value)}
            className='rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-emerald-500'
          />
        </label>

        <label className='flex flex-col gap-2'>
          <span className='text-sm font-medium'>Precio unitario *</span>

          <input
            type='number'
            required
            min='0'
            step='0.01'
            value={unitPrice}
            onChange={(event) => setUnitPrice(event.target.value)}
            className='rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-emerald-500'
          />
        </label>

        <label className='flex flex-col gap-2'>
          <span className='text-sm font-medium'>IVA (%) *</span>

          <input
            type='number'
            required
            min='0'
            max='100'
            step='0.01'
            value={taxRate}
            onChange={(event) => setTaxRate(event.target.value)}
            className='rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-emerald-500'
          />
        </label>

        <label className='flex flex-col gap-2 md:col-span-2'>
          <span className='text-sm font-medium'>Descripción</span>

          <textarea
            maxLength={500}
            rows={4}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            className='resize-none rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-emerald-500'
          />
        </label>

        {error && (
          <p className='rounded-lg border border-red-900 bg-red-950/50 px-4 py-3 text-red-300 md:col-span-2'>
            {error}
          </p>
        )}

        <div className='flex gap-3 md:col-span-2'>
          <button
            type='submit'
            disabled={isSubmitting}
            className='rounded-lg bg-emerald-500 px-5 py-2.5 font-semibold text-slate-950 disabled:opacity-50'
          >
            {isSubmitting
              ? 'Guardando...'
              : isEditing
                ? 'Guardar cambios'
                : 'Crear producto'}
          </button>

          <button
            type='button'
            onClick={onCancel}
            disabled={isSubmitting}
            className='rounded-lg border border-slate-700 px-5 py-2.5'
          >
            Cancelar
          </button>
        </div>
      </form>
    </section>
  );
}

export default ProductForm;
