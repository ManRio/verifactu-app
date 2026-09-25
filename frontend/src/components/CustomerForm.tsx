import { useState } from 'react';
import type { FormEvent } from 'react';

import {
  createCustomer,
  updateCustomer,
  type CreateCustomerData,
} from '../services/customer';
import type { Customer } from '../types/customer';

type CustomerFormProps = {
  customer?: Customer | null;
  onSaved: (customer: Customer) => void;
  onCancel: () => void;
};

function CustomerForm({ customer, onSaved, onCancel }: CustomerFormProps) {
  const [legalName, setLegalName] = useState(customer?.legal_name ?? '');
  const [tradeName, setTradeName] = useState(customer?.trade_name ?? '');
  const [taxId, setTaxId] = useState(customer?.tax_id ?? '');
  const [address, setAddress] = useState(customer?.address ?? '');
  const [postalCode, setPostalCode] = useState(customer?.postal_code ?? '');
  const [city, setCity] = useState(customer?.city ?? '');
  const [province, setProvince] = useState(customer?.province ?? '');
  const [countryCode, setCountryCode] = useState(
    customer?.country_code ?? 'ES',
  );
  const [email, setEmail] = useState(customer?.email ?? '');
  const [phone, setPhone] = useState(customer?.phone ?? '');

  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isEditing = customer != null;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setError('');
    setIsSubmitting(true);

    const data: CreateCustomerData = {
      legal_name: legalName.trim(),
      trade_name: tradeName.trim() || null,
      tax_id: taxId.trim() || null,
      address: address.trim() || null,
      postal_code: postalCode.trim() || null,
      city: city.trim() || null,
      province: province.trim() || null,
      country_code: countryCode.trim().toUpperCase(),
      email: email.trim() || null,
      phone: phone.trim() || null,
    };

    try {
      const savedCustomer = isEditing
        ? await updateCustomer(customer.id, data)
        : await createCustomer(data);

      onSaved(savedCustomer);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : `No se pudo ${isEditing ? 'actualizar' : 'crear'} el cliente`,
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className='mb-8 rounded-2xl border border-slate-800 bg-slate-900 p-6'>
      <div className='mb-6'>
        <h2 className='text-xl font-semibold'>
          {isEditing ? 'Editar cliente' : 'Nuevo cliente'}
        </h2>

        <p className='mt-1 text-sm text-slate-400'>
          {isEditing
            ? 'Modifica los datos del cliente.'
            : 'Añade un cliente a tu negocio.'}
        </p>
      </div>

      <form onSubmit={handleSubmit} className='grid gap-5 md:grid-cols-2'>
        <label className='flex flex-col gap-2'>
          <span className='text-sm font-medium'>Razón social *</span>
          <input
            type='text'
            required
            maxLength={150}
            value={legalName}
            onChange={(event) => setLegalName(event.target.value)}
            className='rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-emerald-500'
          />
        </label>

        <label className='flex flex-col gap-2'>
          <span className='text-sm font-medium'>Nombre comercial</span>
          <input
            type='text'
            maxLength={150}
            value={tradeName}
            onChange={(event) => setTradeName(event.target.value)}
            className='rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-emerald-500'
          />
        </label>

        <label className='flex flex-col gap-2'>
          <span className='text-sm font-medium'>NIF/CIF</span>
          <input
            type='text'
            maxLength={20}
            value={taxId}
            onChange={(event) => setTaxId(event.target.value)}
            className='rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-emerald-500'
          />
        </label>

        <label className='flex flex-col gap-2'>
          <span className='text-sm font-medium'>Email</span>
          <input
            type='email'
            maxLength={254}
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className='rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-emerald-500'
          />
        </label>

        <label className='flex flex-col gap-2'>
          <span className='text-sm font-medium'>Teléfono</span>
          <input
            type='tel'
            maxLength={30}
            value={phone}
            onChange={(event) => setPhone(event.target.value)}
            className='rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-emerald-500'
          />
        </label>

        <label className='flex flex-col gap-2'>
          <span className='text-sm font-medium'>Dirección</span>
          <input
            type='text'
            maxLength={250}
            value={address}
            onChange={(event) => setAddress(event.target.value)}
            className='rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-emerald-500'
          />
        </label>

        <label className='flex flex-col gap-2'>
          <span className='text-sm font-medium'>Código postal</span>
          <input
            type='text'
            maxLength={10}
            value={postalCode}
            onChange={(event) => setPostalCode(event.target.value)}
            className='rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-emerald-500'
          />
        </label>

        <label className='flex flex-col gap-2'>
          <span className='text-sm font-medium'>Localidad</span>
          <input
            type='text'
            maxLength={100}
            value={city}
            onChange={(event) => setCity(event.target.value)}
            className='rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-emerald-500'
          />
        </label>

        <label className='flex flex-col gap-2'>
          <span className='text-sm font-medium'>Provincia</span>
          <input
            type='text'
            maxLength={100}
            value={province}
            onChange={(event) => setProvince(event.target.value)}
            className='rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-emerald-500'
          />
        </label>

        <label className='flex flex-col gap-2'>
          <span className='text-sm font-medium'>País *</span>
          <input
            type='text'
            required
            minLength={2}
            maxLength={2}
            value={countryCode}
            onChange={(event) => setCountryCode(event.target.value)}
            className='rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 uppercase outline-none focus:border-emerald-500'
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
                : 'Crear cliente'}
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

export default CustomerForm;
