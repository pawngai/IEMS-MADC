import * as React from "react";
import { Check, ChevronsUpDown } from "lucide-react";
import { cn } from "@/shared/lib/utils";
import { Input } from "@/shared/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/shared/ui/popover";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandList,
} from "@/shared/ui/command";

const SearchableSelect = ({
  value,
  onValueChange,
  options = [],
  placeholder = "Select...",
  searchPlaceholder = "Search...",
  emptyMessage = "No results found.",
  disabled = false,
  className,
  contentClassName,
  dataTestId,
}) => {
  const [open, setOpen] = React.useState(false);
  const [query, setQuery] = React.useState("");
  const [activeIndex, setActiveIndex] = React.useState(-1);
  const inputRef = React.useRef(null);

  const selected = options.find((option) => option.value === value);
  const normalizedSelected = (selected?.label || "").toLowerCase();
  const normalizedQuery = query.trim().toLowerCase();
  const isQuerying = open && normalizedQuery.length > 0 && normalizedQuery !== normalizedSelected;

  const filteredOptions = React.useMemo(() => {
    if (!isQuerying) return options;
    return options.filter((option) => {
      const searchText = (option.search || `${option.label || ""} ${option.value ?? ""}`)
        .toString()
        .toLowerCase();
      return searchText.includes(normalizedQuery);
    });
  }, [isQuerying, normalizedQuery, options]);

  React.useEffect(() => {
    if (!open) {
      setQuery(selected?.label || "");
      setActiveIndex(-1);
    }
  }, [open, selected]);

  React.useEffect(() => {
    if (activeIndex >= filteredOptions.length) {
      setActiveIndex(filteredOptions.length ? 0 : -1);
    }
  }, [activeIndex, filteredOptions.length]);

  const handleSelect = (option) => {
    onValueChange?.(option.value);
    setQuery(option.label || "");
    setOpen(false);
    setActiveIndex(-1);
  };

  const handleInputChange = (event) => {
    if (disabled) return;
    const next = event.target.value;
    setQuery(next);
    const hasQuery = next.trim().length > 0;
    setOpen(hasQuery);
    setActiveIndex(hasQuery ? 0 : -1);

    const exact = options.find((option) => {
      const label = (option.label || "").toLowerCase();
      const val = (option.value ?? "").toString().toLowerCase();
      const searchVal = next.trim().toLowerCase();
      return searchVal && (label === searchVal || val === searchVal);
    });
    if (exact) {
      onValueChange?.(exact.value);
    }
  };

  const handleKeyDown = (event) => {
    if (disabled) return;
    const hasQuery = query.trim().length > 0;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      if (!hasQuery) return;
      if (!open) setOpen(true);
      setActiveIndex((prev) => {
        if (!filteredOptions.length) return -1;
        if (prev < 0) return 0;
        return (prev + 1) % filteredOptions.length;
      });
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      if (!hasQuery) return;
      if (!open) setOpen(true);
      setActiveIndex((prev) => {
        if (!filteredOptions.length) return -1;
        if (prev < 0) return filteredOptions.length - 1;
        return (prev - 1 + filteredOptions.length) % filteredOptions.length;
      });
    }
    if (event.key === "Enter") {
      if (open && activeIndex >= 0 && filteredOptions[activeIndex]) {
        event.preventDefault();
        handleSelect(filteredOptions[activeIndex]);
      }
    }
    if (event.key === "Escape") {
      if (open) {
        event.preventDefault();
        setOpen(false);
        setQuery(selected?.label || "");
        setActiveIndex(-1);
      }
    }
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <div className={cn("relative w-full", className)}>
          <Input
            ref={inputRef}
            role="combobox"
            aria-expanded={open}
            value={query}
            onChange={handleInputChange}
            onFocus={() => {
              if (disabled) return;
              requestAnimationFrame(() => inputRef.current?.select());
            }}
            onKeyDown={handleKeyDown}
            placeholder={open ? searchPlaceholder : placeholder}
            disabled={disabled}
            data-testid={dataTestId}
            className={cn("w-full pr-8", className)}
          />
          <ChevronsUpDown className="pointer-events-none absolute right-2 top-1/2 h-4 w-4 -translate-y-1/2 opacity-50" />
        </div>
      </PopoverTrigger>
      <PopoverContent
        className={cn("p-0 w-[var(--radix-popover-trigger-width)]", contentClassName)}
        onOpenAutoFocus={(event) => event.preventDefault()}
      >
        <Command shouldFilter={false}>
          <CommandList>
            {filteredOptions.length === 0 ? (
              <CommandEmpty>{emptyMessage}</CommandEmpty>
            ) : (
              <CommandGroup>
                {filteredOptions.map((option, index) => (
                  <CommandItem
                    key={option.value}
                    value={option.search || `${option.label} ${option.value}`}
                    onSelect={() => handleSelect(option)}
                    onMouseEnter={() => setActiveIndex(index)}
                    className={cn(
                      index === activeIndex && "bg-accent text-accent-foreground"
                    )}
                  >
                    <Check
                      className={cn(
                        "mr-2 h-4 w-4",
                        value === option.value ? "opacity-100" : "opacity-0"
                      )}
                    />
                    {option.label}
                  </CommandItem>
                ))}
              </CommandGroup>
            )}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
};

export { SearchableSelect };

