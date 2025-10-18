import React, { useRef, useEffect } from 'react';
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination';

import { Input } from '@/components/ui/input';

interface PaginationProps {
  page: number;
  total: number;
  limit: number;
  onPageChange?: (newPage: number) => void;
  [key: string]: unknown;
}

export function Paginate({ page, total, limit, onPageChange, ...props }: PaginationProps) {
  const totalPages = Math.ceil(total / limit);
  const inputRef = useRef<HTMLInputElement>(null);
  const lastChangeByInput = useRef(false);
  const handlePageChange = (newPage: number, byInput: boolean = false) => {
    if (newPage >= 1 && newPage <= totalPages && newPage !== page && typeof onPageChange === 'function') {
      lastChangeByInput.current = byInput;
      onPageChange(newPage);
    }
  };
  useEffect(() => {
    if (lastChangeByInput.current && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
    lastChangeByInput.current = false;
  }, [page]);

  // Calculate 5 pages around current
  let start = Math.max(1, page - 2);
  let end = Math.min(totalPages, page + 2);
  // Adjust if near start/end
  if (page <= 3) {
    end = Math.min(totalPages, 5);
  } else if (page >= totalPages - 2) {
    start = Math.max(1, totalPages - 4);
  }
  const pages: number[] = [];
  for (let i = start; i <= end; i++) {
    pages.push(i);
  }

  // Build pagination items
  const items = [];
  // First page
  items.push(
    <PaginationItem key="first">
      <PaginationLink
        href="#"
        isActive={page === 1}
        onClick={(e) => {
          e.preventDefault();
          handlePageChange(1);
        }}
      >
        First
      </PaginationLink>
    </PaginationItem>,
  );
  // Prev page
  items.push(
    <PaginationItem key="prev" aria-disabled={page === 1}>
      <PaginationPrevious
        href="#"
        aria-disabled={page === 1}
        onClick={(e) => {
          e.preventDefault();
          if (page > 1) handlePageChange(page - 1);
        }}
        style={page === 1 ? { pointerEvents: 'none', opacity: 0.5 } : {}}
      />
    </PaginationItem>,
  );
  // Ellipsis before
  if (start > 2) {
    items.push(
      <PaginationItem key="ellipsis-before">
        <PaginationEllipsis />
      </PaginationItem>,
    );
  }
  // Pages around current
  for (let i = 0; i < pages.length; i++) {
    if (pages[i] === page) {
      items.push(
        <PaginationItem key={pages[i]}>
          <Input
            ref={inputRef}
            type="number"
            min={1}
            max={totalPages}
            value={page}
            className="w-14 [appearance:textfield] px-2 py-1 text-center [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
            onChange={(e) => {
              const val = Number(e.target.value);
              if (val >= 1 && val <= totalPages && val !== page) {
                handlePageChange(val, true);
              }
            }}
          />
        </PaginationItem>,
      );
    } else {
      items.push(
        <PaginationItem key={pages[i]}>
          <PaginationLink
            href="#"
            isActive={false}
            onClick={(e) => {
              e.preventDefault();
              handlePageChange(pages[i]);
            }}
          >
            {pages[i]}
          </PaginationLink>
        </PaginationItem>,
      );
    }
  }
  // Ellipsis after
  if (end < totalPages - 1) {
    items.push(
      <PaginationItem key="ellipsis-after">
        <PaginationEllipsis />
      </PaginationItem>,
    );
  }
  // Next page
  items.push(
    <PaginationItem key="next" aria-disabled={page === totalPages}>
      <PaginationNext
        href="#"
        aria-disabled={page === totalPages}
        onClick={(e) => {
          e.preventDefault();
          if (page < totalPages) handlePageChange(page + 1);
        }}
        style={page === totalPages ? { pointerEvents: 'none', opacity: 0.5 } : {}}
      />
    </PaginationItem>,
  );
  // Last page
  items.push(
    <PaginationItem key="last">
      <PaginationLink
        href="#"
        isActive={page === totalPages}
        onClick={(e) => {
          e.preventDefault();
          handlePageChange(totalPages);
        }}
      >
        Last
      </PaginationLink>
    </PaginationItem>,
  );

  return (
    <Pagination {...props}>
      <PaginationContent>{items}</PaginationContent>
    </Pagination>
  );
}
