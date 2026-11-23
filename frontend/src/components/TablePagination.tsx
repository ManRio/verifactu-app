type Props = {
  currentPage: number;
  totalItems: number;
  onPageChange: (page: number) => void;
  pageSize?: number;
};

export const TABLE_PAGE_SIZE = 10;

export default function TablePagination({
  currentPage, totalItems, onPageChange, pageSize = TABLE_PAGE_SIZE,
}: Props) {
  const pages = Math.max(1, Math.ceil(totalItems / pageSize));
  const safePage = Math.max(1, Math.min(currentPage, pages));
  if (pages < 2) return <p className='mt-4 text-xs text-slate-500'>{totalItems} registros</p>;
  const start = Math.max(1, safePage - 2);
  const end = Math.min(pages, Math.max(start + 4, safePage + 2));
  return (
    <nav aria-label='Paginación del listado' className='mt-5 flex flex-wrap items-center justify-between gap-3 text-sm text-slate-300'>
      <span>{(safePage - 1) * pageSize + 1}–{Math.min(safePage * pageSize, totalItems)} de {totalItems} registros</span>
      <div className='flex flex-wrap gap-2'>
        <button type='button' disabled={safePage === 1} onClick={() => onPageChange(safePage - 1)} className='rounded-lg border border-slate-700 px-3 py-2 hover:bg-slate-800 disabled:opacity-40'>Anterior</button>
        {Array.from({ length: end - start + 1 }, (_, index) => start + index).map((page) => (
          <button key={page} type='button' onClick={() => onPageChange(page)} aria-current={page === safePage ? 'page' : undefined}
            className={`rounded-lg px-3 py-2 ${page === safePage ? 'bg-emerald-400 font-bold text-slate-950' : 'border border-slate-700 hover:bg-slate-800'}`}>
            {page}
          </button>
        ))}
        <button type='button' disabled={safePage === pages} onClick={() => onPageChange(safePage + 1)} className='rounded-lg border border-slate-700 px-3 py-2 hover:bg-slate-800 disabled:opacity-40'>Siguiente</button>
      </div>
    </nav>
  );
}
